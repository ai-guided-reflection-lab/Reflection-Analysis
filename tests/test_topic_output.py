import contextlib
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.controller.gpt_api import Model, PromptConfig
from application.model.services.topic_output import TOPIC_OUTPUT_SCHEMA, validate_topic_output


class TopicOutputTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.valid = {
            'primary_labels_selected': ['none'],
            'resolution_primary_labels': ['no_challenge'],
            'urgency': 'none', 'reflection_summary': 'No challenges reported.',
            'instructor_suggestions': 'No action needed.',
        }
        self.ref = SimpleNamespace(id='test', console_output=lambda: 'No challenges')

    def test_valid_no_challenge_and_invalid_shapes(self):
        self.assertEqual(validate_topic_output(json.dumps(self.valid)), self.valid)
        for value in ({'fields': self.valid}, {}, {'primary_labels_selected': []},
                      dict(self.valid, primary_labels_selected=[{'label': 'none'}]),
                      dict(self.valid, resolution_primary_labels=[]),
                      dict(self.valid, resolution_primary_labels=['no_challenge', 'resolved']),
                      dict(self.valid, reflection_summary={}), 'not json'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_topic_output(value)

    def run_batch(self):
        return PromptConfig('application/model/prompts/topic_analysis.json').run_prompt_on_individual_refs(
            [self.ref], provider='groq', output_schema=TOPIC_OUTPUT_SCHEMA,
            output_validator=validate_topic_output)

    def test_retry_recovers_wrong_shape_and_keeps_prompt_json(self):
        with patch.object(Model, 'prompt', side_effect=['{}', json.dumps(self.valid)]) as prompt:
            results = self.run_batch()
        self.assertEqual(len(results), 1)
        self.assertEqual(json.loads(results[0]), self.valid)
        self.assertEqual(prompt.call_count, 2)
        source = json.loads(prompt.call_args_list[0].args[0])
        self.assertIsInstance(source['labels_and_descriptions']['output_instructions']['fields']['primary_labels_selected'], list)
        self.assertIn('failed validation', prompt.call_args_list[1].args[0])

    def test_retry_is_bounded(self):
        with patch.object(Model, 'prompt', return_value='{}') as prompt:
            with self.assertRaisesRegex(RuntimeError, 'Invalid topic output after one retry'):
                self.run_batch()
        self.assertEqual(prompt.call_count, 2)

    def test_api_failure_is_not_schema_retried(self):
        with patch.object(Model, 'prompt', side_effect=RuntimeError('quota exceeded')) as prompt:
            with self.assertRaisesRegex(RuntimeError, 'quota exceeded'):
                self.run_batch()
        self.assertEqual(prompt.call_count, 1)

    def test_strict_schema_for_supported_models_and_json_fallback(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content=json.dumps(self.valid)))])
        for model, expected in [('openai/gpt-oss-20b', 'json_schema'),
                                ('openai/gpt-oss-120b', 'json_schema'),
                                ('custom-model', 'json_object')]:
            with self.subTest(model=model), patch('application.controller.gpt_api.get_client', return_value=client):
                Model.prompt('Classify', 'No challenges', model=model, provider='groq', output_schema=TOPIC_OUTPUT_SCHEMA)
                args = client.chat.completions.create.call_args.kwargs
                self.assertEqual(args['response_format']['type'], expected)
                self.assertIn('primary_labels_selected', args['messages'][0]['content'])
                if expected == 'json_schema':
                    self.assertTrue(args['response_format']['json_schema']['strict'])
                    self.assertEqual(args['response_format']['json_schema']['schema'], TOPIC_OUTPUT_SCHEMA)
