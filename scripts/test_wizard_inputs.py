import builtins
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.wizard import run_setup_wizard
import config.wizard as wizmod
# Disable clear_screen during automated tests so console output isn't wiped
wizmod.clear_screen = lambda: None

TEST_CONFIG_PATH = Path('config_test.json')


def simulate(inputs):
    it = iter(inputs)
    original_input = builtins.input
    def fake_input(prompt=''):
        try:
            return next(it)
        except StopIteration:
            return ''
    builtins.input = fake_input
    try:
        res = run_setup_wizard(str(TEST_CONFIG_PATH))
    finally:
        builtins.input = original_input
    return res


if __name__ == '__main__':
    # Clean up
    try:
        TEST_CONFIG_PATH.unlink()
    except Exception:
        pass

    print('--- Test: choose n (skip wizard) ---')
    r = simulate(['n'])
    print('Result is None?', r is None)
    print('Config file exists after n?', TEST_CONFIG_PATH.exists())
    if TEST_CONFIG_PATH.exists():
        print('Config contents keys:', list(json.loads(TEST_CONFIG_PATH.read_text()).keys()))

    # remove file
    try:
        TEST_CONFIG_PATH.unlink()
    except Exception:
        pass

    print('\n--- Test: choose q (quit) ---')
    r2 = simulate(['q'])
    print('Result is None?', r2 is None)
    print('Config file exists after q?', TEST_CONFIG_PATH.exists())
