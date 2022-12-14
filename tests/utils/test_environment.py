from Babylon.utils.environment import Environment


def test_init():
    """Testing Environment"""
    env = Environment()
    assert env.configuration
    assert env.working_dir
