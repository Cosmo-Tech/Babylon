from Babylon.utils.environment import Environment


def test_init():
    """Testing Environment"""
    env = Environment(True, True)
    assert env.configuration
    assert env.working_dir
