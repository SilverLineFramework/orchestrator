
import os
import sys
import shlex
import subprocess
import threading

import asyncio
import clauncher.settings as settings
import time

class FileType():   
    WA = 'WASM'
    PY = 'PY'

class ModuleLaucher():

    def _run_thread(self, cmd, env):
        subprocess.run(cmd, env=env)
                     
    def run(self, module, dbg_topic, done_topic, done_msg):
        cmd = []
        
        if (module.filetype == FileType.PY):
            cmd.append(settings.s_dict['runtime']['py_launcher_path']) 
        elif (module.filetype == FileType.WA):
            cmd.append(settings.s_dict['runtime']['wasm_launcher_path'])

        stdin_topic = dbg_topic+'/stdin/'+module.uuid
        stdout_topic = dbg_topic+'/stdout/'+module.uuid

        env = { 
                'mqtt_srv' : shlex.quote(settings.s_dict['mqtt_server']['host']), 
                'filename': shlex.quote(module.filename), 
                'fid': shlex.quote(module.fileid), 
                'pipe_stdin_stdout': 'True', 
                'sub_topic': shlex.quote(stdin_topic),
                'pub_topic': shlex.quote(stdout_topic),
                'args': shlex.quote(module.args),
                'done_topic': shlex.quote(done_topic),
                'done_msg': shlex.quote(done_msg)}
        
        print('env=',env)
        t = threading.Thread(target=self._run_thread, args=(cmd, env))
        t.start()
                   
def main():
    settings.load()
    m = ModuleLaucher()
    m.run('test.zip', '1mcJhBvnNqs1CpNsZG2QUjhk3_8SS7Q7U', FileType.PY, 'realm/proc/stdin', 'realm/proc/stdout', '')
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()