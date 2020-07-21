
class COLOR:
    @staticmethod
    def BOLD(string): return f'\1\33[1m{string}\33[0m\2'
    @staticmethod
    def ITALIC(string): return f'\1\33[3m{string}\33[0m\2'
    @staticmethod
    def URL(string): return f'\1\33[4m{string}\33[0m\2'
    @staticmethod
    def BLINK(string): return f'\1\33[5m{string}\33[0m\2'
    @staticmethod
    def BLINK2(string): return f'\1\33[6m{string}\33[0m\2'
    @staticmethod
    def SELECTED(string): return f'\1\33[7m{string}\33[0m\2'
    @staticmethod
    def BLACK(string): return f'\1\33[30m{string}\33[0m\2'
    @staticmethod
    def RED(string): return f'\1\33[31m{string}\33[0m\2'
    @staticmethod
    def GREEN(string): return f'\1\33[32m{string}\33[0m\2'
    @staticmethod
    def YELLOW(string): return f'\1\33[33m{string}\33[0m\2'
    @staticmethod
    def BLUE(string): return f'\1\33[34m{string}\33[0m\2'
    @staticmethod
    def VIOLET(string): return f'\1\33[35m{string}\33[0m\2'
    @staticmethod
    def BEIGE(string): return f'\1\33[36m{string}\33[0m\2'
    @staticmethod
    def WHITE(string): return f'\1\33[37m{string}\33[0m\2'
    @staticmethod
    def BLACKBG(string): return f'\1\33[40m{string}\33[0m\2'
    @staticmethod
    def REDBG(string): return f'\1\33[41m{string}\33[0m\2'
    @staticmethod
    def GREENBG(string): return f'\1\33[42m{string}\33[0m\2'
    @staticmethod
    def YELLOWBG(string): return f'\1\33[43m{string}\33[0m\2'
    @staticmethod
    def BLUEBG(string): return f'\1\33[44m{string}\33[0m\2'
    @staticmethod
    def VIOLETBG(string): return f'\1\33[45m{string}\33[0m\2'
    @staticmethod
    def BEIGEBG(string): return f'\1\33[46m{string}\33[0m\2'
    @staticmethod
    def WHITEBG(string): return f'\1\33[47m{string}\33[0m\2'
    @staticmethod
    def GREY(string): return f'\1\33[90m{string}\33[0m\2'
    @staticmethod
    def RED2(string): return f'\1\33[91m{string}\33[0m\2'
    @staticmethod
    def GREEN2(string): return f'\1\33[92m{string}\33[0m\2'
    @staticmethod
    def YELLOW2(string): return f'\1\33[93m{string}\33[0m\2'
    @staticmethod
    def BLUE2(string): return f'\1\33[94m{string}\33[0m\2'
    @staticmethod
    def VIOLET2(string): return f'\1\33[95m{string}\33[0m\2'
    @staticmethod
    def BEIGE2(string): return f'\1\33[96m{string}\33[0m\2'
    @staticmethod
    def WHITE2(string): return f'\1\33[97m{string}\33[0m\2'
    @staticmethod
    def GREYBG(string): return f'\1\33[100m{string}\33[0m\2'
    @staticmethod
    def REDBG2(string): return f'\1\33[101m{string}\33[0m\2'
    @staticmethod
    def GREENBG2(string): return f'\1\33[102m{string}\33[0m\2'
    @staticmethod
    def YELLOWBG2(string): return f'\1\33[103m{string}\33[0m\2'
    @staticmethod
    def BLUEBG2(string): return f'\1\33[104m{string}\33[0m\2'
    @staticmethod
    def VIOLETBG2(string): return f'\1\33[105m{string}\33[0m\2'
    @staticmethod
    def BEIGEBG2(string): return f'\1\33[106m{string}\33[0m\2'
    @staticmethod
    def WHITEBG2(string): return f'\1\33[107m{string}\33[0m\2'
