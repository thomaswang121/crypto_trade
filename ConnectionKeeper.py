import time

class Connection(object):
    stop_flag = False

    @classmethod
    def ping_server(cls, **kwargs):
        while(True):
            try:
                kwargs['rs'].futures_ping()
                cls.stop_flag = False
                
            except:
                cls.stop_flag = True

            time.sleep(10)
    
    @staticmethod
    def refresh_websocket(rs):
        rs.futures_stream_keepalive()
        pass
        