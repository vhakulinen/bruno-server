from include.commands.decorators import Args as cmd_args


class Args(cmd_args):
    def __call__(self, func):
        def wrapper(args):
            if self.no_args == len(args):
                func(args)
            else:
                if self.msg:
                    print(self.msg)
                else:
                    print("Invalid arguments")
        return wrapper
