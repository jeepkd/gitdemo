import unittest
import application
import json
from shared.database import mongo


class TestPredictionAPIV2(unittest.TestCase):
    def setUp(self):
        self.app = application.create_app(config_object='config.ConfigTesting')
        self.client = self.app.test_client()
        self.headers = {'Api-Key': self.app.config['API_KEY']}
        self.valid_img_url = 'http://placehold.it/299x299.jpg'
        self.valid_predictor = 'nanameue'

    def tearDown(self):
        with self.app.app_context():
            mongo.db.predictions.delete_many({})

    def _get(self, url):
        return self.client.get(url, headers=self.headers)

    def _patch(self, url, data={}):
        return self.client.patch(url, data=data, headers=self.headers)

    def _create_a_prediction(self, **kwargs):
        return self.client.post(
            'api/v2/predictions', data=kwargs, headers=self.headers)

    def _create_a_valid_prediction(self):
        return self._create_a_prediction(
            img_url=self.valid_img_url, predictor=self.valid_predictor)

    def test_get_status_is_ok(self):
        result = json.loads(self._get('/status').data)
        assert result['status'] == 200
        assert result['message'] == 'OK'

    def test_get_root_contains_api_docs(self):
        result = self._get('/').data
        assert '<title>Kiyo Prime API</title>' in result

    def test_post_predictions_create(self):
        result = self._create_a_valid_prediction()
        assert 'prediction_id' in result.data
        with self.app.app_context():
            assert mongo.db.predictions.find({}).count() == 1

    def test_post_predictions_missing_params(self):
        result = self._create_a_prediction(img_url=self.valid_img_url)
        assert 'Missing required parameter' in result.data
        assert 'predictor' in result.data

        result = self._create_a_prediction(predictor=self.valid_predictor)
        assert 'Missing required parameter' in result.data
        assert 'img_url' in result.data

    def test_post_predictions_bad_choice_predictor(self):
        result = self._create_a_prediction(img_url=self.valid_img_url,
                                           predictor='wrong_predictor_name')
        assert 'wrong_predictor_name' in result.data
        assert 'is not a valid choice' in result.data

    def test_get_prediction_list(self):
        for i in range(5):
            self._create_a_valid_prediction()
        result = self._get('api/v2/predictions')
        pred_list = json.loads(result.data)
        assert len(pred_list) == 5
        assert pred_list[0]['_id'] > pred_list[1]['_id'], 'Should list latest predictions first.'

    def test_get_prediction(self):
        result = self._create_a_valid_prediction()
        pred_id = json.loads(result.data).get('prediction_id')
        result = self._get('api/v2/predictions/{}'.format(pred_id))
        assert pred_id in result.data

    def test_patch_prediction_update(self):
        result = self._create_a_valid_prediction()
        pred_id = json.loads(result.data).get('prediction_id')

        data = {'human_answer': 'test_label'}
        result = self._patch('api/v2/predictions/{}'.format(pred_id), data=data)
        assert pred_id in result.data
        assert 'updated_at' in result.data
        assert json.loads(result.data)['human_answer'] == 'test_label'

        # result = self._create_a_valid_prediction()
        # pred_id = json.loads(result.data).get('prediction_id')
        # img_url = 'https://test.domain/file.jpg'
        # data = {'img_url': img_url}
        # result = self._patch('api/v2/predictions/{}'.format(pred_id), data=data)
        # assert json.loads(result.data)['img_url'] == img_url


if __name__ == '__main__':
    unittest.main()
