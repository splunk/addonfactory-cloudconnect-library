## Generator Script to build Sample TA
The sample TAs present in this directory are meant to test the functionalities of cloudconnectlib library. In order to build the sample TAs to test the features of cloudconnectlib, execute the below steps:
1. Make sure you are present in the current directory while building the sample TA.
2. A generator script named "build_sample_ta.py" is present in this directory. In order to get familiar with this script, execute the command: `python build_sample_ta.py`
3. Execute the generator script to build the add-on: `python build_sample_ta.py <sample_ta_name> <python_version>`
   - <sample_ta_name>: Provide name of one of the Sample TAs present in the directory
   - <python_version>: Provide a python version which will be supported by the Sample TA. Allowed values are "python2" and "python3". Default value is "python2"
4. On successful execution of the script, an archived file of the Sample TA gets generated, which can be uploaded on the splunk instance and the user can utilize it to test the functionalities of the cloudconnectlib library.

### Example of generator script execution
![Execution of generator script](generator_script_working.png)
