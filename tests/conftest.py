
def pytest_collection_modifyitems(config, items):
    """
    Modifies the order of tests to run tests marked with 'pyinstaller_build' last.
    """
    pyinstaller_build_tests = []
    other_tests = []
    for item in items:
        if item.get_closest_marker("pyinstaller_build"):
            pyinstaller_build_tests.append(item)
        else:
            other_tests.append(item)
    
    items[:] = other_tests + pyinstaller_build_tests
