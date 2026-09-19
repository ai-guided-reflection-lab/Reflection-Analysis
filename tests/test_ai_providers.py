import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.controller import gpt_api
from application.model.services.data_processing import DataProcessingService


class ProviderTests(unittest.TestCase):
    def test_clients_use_separate_keys_and_endpoints(self):
        with patch.dict(os.environ, {'GROQ_API_KEY': 'groq-test', 'OPENAI_API_KEY': 'openai-test'}, clear=True), \
             patch.dict(gpt_api._clients, {}, clear=True), \
             patch.object(gpt_api, 'OpenAI') as constructor:
            gpt_api.get_client('groq')
            constructor.assert_called_with(api_key='groq-test', base_url='https://api.groq.com/openai/v1')
            gpt_api.get_client()
            constructor.assert_called_with(api_key='openai-test', base_url='https://api.openai.com/v1')
            self.assertEqual(constructor.call_count, 2)

    def test_groq_missing_key_does_not_fall_back_to_openai(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-test'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'GROQ_API_KEY'):
                gpt_api.get_client('groq')

    def test_groq_request_parameters_and_response(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content='{"ok": true}'))])
        with patch.object(gpt_api, 'get_client', return_value=client) as get_client:
            result = gpt_api.Model.prompt('Classify', 'Answer', provider='groq',
                                          model='openai/gpt-oss-20b', max_tokens=4096)
        get_client.assert_called_once_with('groq')
        args = client.chat.completions.create.call_args.kwargs
        self.assertEqual(args['max_completion_tokens'], 4096)
        self.assertNotIn('max_tokens', args)
        self.assertEqual(args['response_format'], {'type': 'json_object'})
        self.assertEqual(args['reasoning_effort'], 'low')
        self.assertIn('JSON', args['messages'][0]['content'])
        self.assertEqual(result, '{"ok": true}')

    def test_truncated_response_fails(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(finish_reason='length', message=SimpleNamespace(content='{"ok":'))])
        with patch.object(gpt_api, 'get_client', return_value=client):
            with self.assertRaisesRegex(ValueError, 'token limit'):
                gpt_api.Model.prompt('Classify', 'Answer', provider='groq')

    def test_service_forwards_provider_and_custom_model(self):
        with patch.object(gpt_api.PromptConfig, 'run_prompt_on_individual_refs', return_value=[{}]) as run:
            DataProcessingService().analyze_topics([Mock()], provider='groq', model='custom-model')
        self.assertEqual(run.call_args.kwargs['provider'], 'groq')
        self.assertEqual(run.call_args.kwargs['model'], 'custom-model')
        self.assertEqual(run.call_args.kwargs['max_tokens'], 4096)


if __name__ == '__main__':
    unittest.main()
