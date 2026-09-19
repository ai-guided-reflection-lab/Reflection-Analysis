import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

from application.controller.gpt_api import Model, PromptConfig
from application.model.services.data_processing import DataProcessingService
from application.view.analysis_UI.topic_analysis import TopicAnalysisManager


class TopicAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.output))
        self.enterContext(contextlib.redirect_stderr(self.output))
        self.ui = self.enterContext(patch('application.view.analysis_UI.topic_analysis.st'))
        self.ui.session_state = SimpleNamespace()
        self.ref = SimpleNamespace(id='student@example.test', questions=['Question'],
                                   reflections=['Answer'], console_output=lambda: 'Answer')
        self.processor = Mock()
        self.processor.load_reflection_data.return_value = [self.ref]
        self.manager = TopicAnalysisManager(SimpleNamespace(base_path=self.tmp.name),
                                            self.processor, None)
        self.path = Path(self.tmp.name) / 'IS32/ref1/results/IS32_ref1_exploded.csv'

    def test_invalid_results_fail_and_preserve_previous_file(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text('previous results')
        for results in ([], ['invalid json'], [{}], ['[]'],
                        [{'primary_labels_selected': []}],
                        [{'primary_labels_selected': [None]}]):
            with self.subTest(results=results):
                self.processor.analyze_topics.return_value = results
                self.assertFalse(self.manager.run_analysis('IS32', 'ref1'))
                self.assertEqual(self.path.read_text(), 'previous results')
                self.ui.error.assert_called()

    def test_valid_results_create_csv(self):
        self.processor.analyze_topics.return_value = [{
            'primary_labels_selected': ['python_and_coding'],
            'resolution_primary_labels': ['unresolved'], 'urgency': 'low'}]
        self.assertTrue(self.manager.run_analysis('IS32', 'ref1'))
        result = pd.read_csv(self.path)
        self.assertEqual(result.iloc[0]['ID'], self.ref.id)
        self.assertEqual(result.iloc[0]['primary_labels_selected'], 'python_and_coding')

    def test_api_failure_reaches_ui(self):
        self.processor = DataProcessingService()
        self.manager.data_processor = self.processor
        with patch.object(self.processor, 'load_reflection_data', return_value=[self.ref]), \
             patch.object(Model, 'prompt', side_effect=RuntimeError('API quota exceeded')):
            self.assertFalse(self.manager.run_analysis('IS32', 'ref1'))
        self.assertIn('API quota exceeded', self.ui.error.call_args.args[0])
        self.assertFalse(self.path.exists())

    def test_partial_api_failure_is_not_success(self):
        with patch.object(Model, 'prompt', side_effect=['{}', RuntimeError('API unavailable')]):
            with self.assertRaisesRegex(RuntimeError, 'failed after 1 of 2'):
                PromptConfig('application/model/prompts/topic_analysis.json').run_prompt_on_individual_refs(
                    [self.ref, self.ref])

    def test_zero_limit_means_all(self):
        with patch.object(PromptConfig, 'run_prompt_on_individual_refs', return_value=[{}]) as run:
            DataProcessingService().analyze_topics([self.ref], num_reflections=0)
        self.assertEqual(run.call_args.kwargs['refs'], [self.ref])

    def test_groq_analysis_saves_results(self):
        self.manager.data_processor = DataProcessingService()
        with patch.object(self.manager.data_processor, 'load_reflection_data', return_value=[self.ref]), \
             patch.object(Model, 'prompt', return_value='{"primary_labels_selected": ["python_and_coding"]}') as prompt:
            self.assertTrue(self.manager.run_analysis('IS32', 'ref1', provider='groq', model='custom-model'))
        self.assertEqual(prompt.call_args.kwargs['provider'], 'groq')
        self.assertEqual(prompt.call_args.kwargs['model'], 'custom-model')
        self.assertTrue(self.path.is_file())


if __name__ == '__main__':
    unittest.main()
