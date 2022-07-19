import pathlib
from typing import List, Any
from datetime import datetime
import json

class StrategyBase(object):
    def __init__(self) -> None:
        
        # folder of this strategy                                    
        self._folder = pathlib.Path().cwd() / self.strategy_id
        if not self._folder.exists():                            
            self._folder.mkdir(parents=True, exist_ok=True) 

    def check_param_exists(self, param) -> None:
        if not hasattr(self, param):
            raise ValueError(f"The parameter {param} is not defined in the class.")       

    def set_check_inputs(self, param, value) -> None:
        self.check_param_exists(param)
        if (not isinstance(value, type(getattr(self, param)))):
            raise TypeError(
                f"The parameter {param} takes data type {type(getattr(self, param))}."
            )

    def get(self, param) -> Any:
        self.check_param_exists(param)
        return getattr(self, param)

    def write_transaction_log(self, transaction_record):
        file_path = self._folder / f"{datetime.now().strftime('%Y-%m-%d')}_transaction.log"
        f = open(file_path, 'a')
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {transaction_record}\n")
        f.close()

    def _save_data(self, **kwargs):
        file_path = self._folder / 'last_trading_status.json'
        f = open(file_path, 'w')
        json.dump(kwargs, f, indent=4)
        f.close()