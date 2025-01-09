from omegaconf import OmegaConf, DictConfig

def sum_of_dict_values(d : dict) -> int:
    return sum(d.values())

def register_resolvers():
    OmegaConf.register_new_resolver("eval", eval) 
    OmegaConf.register_new_resolver("sum_of_dict_values", sum_of_dict_values)