import Preprocessing as pre
import time



name = 'periodogram'

params = pre.get_required_params(name)
functions = pre.get_functions()
doc = functions[name].__doc__ if functions[name].__doc__ else "No documentation available"
    

start_time = time.time()
pre.extract_params_and_returns(doc)
end_time = time.time()
elapsed = end_time - start_time
print(f"chat: {elapsed:.6f} seconds")

start_time = time.time()
pre.extract_params_and_returns2(doc)
end_time = time.time()
elapsed = end_time - start_time
print(f"t3: {elapsed:.6f} seconds")

