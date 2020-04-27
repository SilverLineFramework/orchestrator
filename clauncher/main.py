import time
from clauncher.mqttmng import MqttManager

import clauncher.settings as settings
from clauncher.runtime import Runtime

def main():
    settings.load()

    rt = Runtime(rt_name=settings.s_dict['runtime']['name'], rt_max_nmodules=settings.s_dict['runtime']['max_nmodules'], rt_apis=settings.s_dict['runtime']['apis'])
    mqttc = MqttManager(rt)

    mqttc.start(settings.s_dict['mqtt_server']['host'])    

    while True:
        time.sleep(60)
        
if __name__ == "__main__":
    main()