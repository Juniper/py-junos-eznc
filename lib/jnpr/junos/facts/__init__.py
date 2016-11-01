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
            if key not in callbacks:
                callbacks[key] = module.get_facts
            else:
                raise RuntimeError('Both the %s module and the %s module claim '
                                   'to provide the %s fact. Please report this '
                                   ' error.' %
                                   (callbacks[key].__module__,
                                    module.__name__,
                                    key))
    return callbacks

_callbacks = _build_fact_callbacks()