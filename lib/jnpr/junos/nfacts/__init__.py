import os
import importlib

def _get_list_of_fact_module_names():
    module_names = []
    facts_dir = os.path.dirname(__file__)
    for file in os.listdir(facts_dir):
        if (os.path.isfile(os.path.join(facts_dir,file)) and
            not os.path.islink(os.path.join(facts_dir,file))):
            if file.endswith('.py') and not file.startswith('_'):
                (module_name,_) = file.rsplit('.py',1)
                module_names.append('%s.%s' % (__name__,module_name))
    return module_names

def _import_fact_modules():
    modules = []
    for name in _get_list_of_fact_module_names():
        modules.append(importlib.import_module(name))
    return modules

def _build_fact_callbacks():
    callbacks = {}
    for module in _import_fact_modules():
        for key in module.provides_facts():
            callbacks[key] = module.get_facts
    return callbacks

_callbacks = _build_fact_callbacks()