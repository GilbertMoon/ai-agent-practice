import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chat_loop import serve
from main import MockClient, Reply


class FakeLiveClient:
    def ask(self, question):
        return Reply(text="테스트 전용 응답", model="fake", input_tokens=3,
                     output_tokens=4, cached_input_tokens=0, measurement_mode="live")


class FailingClient:
    def ask(self, question):
        raise ConnectionError("DO_NOT_PRINT_SECRET")


def run_inputs(client, questions):
    iterator = iter(questions)
    output = []
    serve(client, read=lambda prompt: next(iterator), write=output.append)
    return "\n".join(output)


class ChatLoopTests(unittest.TestCase):
    def test_mock_multiple_questions(self):
        out = run_inputs(MockClient(), ["첫 질문", "두 번째 질문", "exit"])
        self.assertIn("첫 질문", out)
        self.assertIn("두 번째 질문", out)
        self.assertIn("Mock 모드", out)

    def test_empty_help_and_quit(self):
        out = run_inputs(MockClient(), [" ", "help", "quit"])
        self.assertIn("질문을 입력해 주세요.", out)
        self.assertIn("빈 질문은 보내지 않습니다.", out)

    def test_live_usage_display_with_fake_client(self):
        out = run_inputs(FakeLiveClient(), ["안녕", "exit"])
        self.assertIn("input=3", out)
        self.assertIn("cached_input=0", out)

    def test_error_message_redacts_detail(self):
        out = run_inputs(FailingClient(), ["안녕", "exit"])
        self.assertIn("ConnectionError", out)
        self.assertNotIn("DO_NOT_PRINT_SECRET", out)

    def test_eof_exits(self):
        outputs = []
        serve(MockClient(), read=lambda p: (_ for _ in ()).throw(EOFError()), write=outputs.append)
        self.assertIn("대화를 종료합니다.", "\n".join(outputs))


if __name__ == "__main__":
    unittest.main()
