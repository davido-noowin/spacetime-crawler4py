import os
from spacetime import Node
from utils.pcc_models import Register


# TODO ANGELA: ARE THESE NUMBERS GOOD?
# stop program if server takes too long to connect
import timeout_decorator            # pip install timeout-decorator
MAX_SERVER_TIMEOUT = 20             # timeout period for the server
# AI Tutor suggested to use the timeout_decorator package (information on timeout_decorator was found through this link: https://pypi.org/project/timeout-decorator/)


def init(df, user_agent, fresh):
    reg = df.read_one(Register, user_agent)
    if not reg:
        reg = Register(user_agent, fresh)
        df.add_one(Register, reg)
        df.commit()
        df.push_await()
    while not reg.load_balancer:
        df.pull_await()
        if reg.invalid:
            raise RuntimeError("User agent string is not acceptable.")
        if reg.load_balancer:
            df.delete_one(Register, reg)
            df.commit()
            df.push()
    return reg.load_balancer


@timeout_decorator.timeout(MAX_SERVER_TIMEOUT) # if a server exceeds the timeout period, timeout_decorator.TimeoutError is raised
def get_cache_server(config, restart):
    init_node = Node(
        init, Types=[Register], dataframe=(config.host, config.port))
    return init_node.start(
        config.user_agent, restart or not os.path.exists(config.save_file))