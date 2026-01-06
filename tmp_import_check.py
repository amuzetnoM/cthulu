import importlib,traceback

try:
    import cthulu.__main__
    print('OK_MAIN')
except Exception:
    traceback.print_exc()
    print('MAIN_FAIL')

try:
    import cthulu.llm
    print('OK_LLM')
except Exception:
    traceback.print_exc()
    print('LLM_FAIL')
