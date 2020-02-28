# -*- coding: utf-8 -*-
import os
import sys
import yaml
from threading import Lock
from collections import Iterable


def open_file(fp, *args, **kargs):
    '''open file, 适配python 2 和 3'''
    if sys.version_info[0] >= 3:
        kargs['encoding'] = 'utf8'
        return open(fp, *args, **kargs)
    else:
        return open(fp, *args, **kargs)


class ConfigYaml:
    '''基于Yaml的配置类.
    cy = ConfigYaml('xxx/xxx.yaml')
    cy.get_config('key1.key2.key3', default_value)
    cy.set_config('key1.key2.key3', new_value)
    cy.flush() 
    '''

    def __init__(self, config_file):
        self.config_file = config_file
        self._cache = None
        self.mutex = Lock()

    def __setitem__(self, key, value):
        '''实现访问器.'''
        self.set_config(key, value)

    def __getitem__(self, key):
        '''实现访问器.'''
        return self.get_config(key, None)

    def get(self, key, defval=None):
        '''实现访问器. 带默认值。'''
        return self.get_config(key, defval)

    def _update_config(self, from_, to_):
        if isinstance(from_, dict) and isinstance(to_, dict):
            for key, val_to in to_.items():
                if key not in from_:
                    continue
                val_from = from_[key]
                if isinstance(val_from, dict) and isinstance(val_to, dict):
                    self._update_config(val_from, val_to)
                else:
                    to_[key] = val_from

    @property
    def config_path(self):
        '''当前配置文件的路径'''
        return self.config_file

    def get_config(self, key, defval):
        '''返回配置项的值，如果配置不存在，返回defval.'''
        if self._cache is None:
            with self.mutex:
                fp = self.config_path
                if not os.path.exists(fp):
                    return defval

                with open_file(fp) as ff:
                    self._cache = yaml.load(ff) or {}

        v = self._cache
        for k in key.split('.'):
            if not isinstance(v, Iterable):
                return defval
            if k not in v:
                return defval
            v = v[k]

        if isinstance(v, list):
            return v[:]
        if isinstance(v, dict):
            return v.copy()
        return v

    def flush(self):
        '''将配置写入磁盘文件。'''
        with self.mutex:
            fp = self.config_path
            with open_file(fp, 'w+') as ffw:
                yaml.dump(self._cache, ffw, allow_unicode=True,
                          indent=4, default_flow_style=False)

    def set_config(self, key, val, flush=False):
        '''设置配置'''
        with self.mutex:
            # update the cache
            if self._cache is None:
                fp = self.config_path
                if not os.path.exists(fp):
                    return

                with open_file(fp) as ff:
                    self._cache = yaml.load(ff) or {}

            if self._cache:
                v = self._cache
                for k in key.split('.')[:-1]:
                    if k not in v:
                        v[k] = {}
                    v = v[k]
                v[key.split('.')[-1]] = val

            if flush:
                fp = self.config_path
                with open_file(fp, 'w+') as ffw:
                    yaml.dump(self._cache, ffw, allow_unicode=True,
                              indent=4, default_flow_style=False)

