# Vulnerability Finder for AI Enabled Medical Devices

This is a automated tool to identify vulnerabilities in AI Enabled Medical Devices

## FDA_Scraper.py

* This is a automated script to download the Excel file containing information of the devices and also download all the Summary pdfs available
* It relies on selenium to extract the information from internet
* Due to few problems with downloading files through selenium it is recommended to download the execel file directly and place it in `Data/Downloads` Directory with the name `Artificial Intelligence and Machine Learning (AIML)-Enabled Medical Devices FDA.xlsx`

## PDF_Reader.py & PDF_Reader_2.py

* This is code to read the contents of the pdf
* This has a reader object which takes input as path of the pdf and then you can use the functions in the class to extract the information
* Currently only version 2 is used since its more better pdf parser library than what is available in version 1

## Table_Reader.py

* This is the file to extract contents of tables in the pdf if existent
* Again this provides a reader object to get the tables
* This is not currently used in the code since even tabular data is treated as paragraphs

## Model.py

* This is the main file where the Data Analysing Model exist for the Questionarre
* Multiple advanced/LLM API's can be used here for interpretation
* Currently we are using opensource `BERT Model` based on `Squad` dataset 

## Browser.py

* This is a script to manage scraping and interacting with selenium docker
* It also allows to perform google search and return first 2(can be modified) results

## Helper_functions.py

* Common library to handle helper functions used frequently and in one or more scripts

## LLM.py

* Library to handle interface with LLMs. Currently supports use of GPT4ALL models and has implicit parsing methods for the responses generated
* Included basic functionality to also use ChatGPT API. Not used currently

## Scholar_scraper.py

* Library to handle interface with google scholar
* Can be used to include other scholarly search engines too
* Support of proxy usage exists. Only can work with premium proxies. Doesnt work with free proxies
## settings.py

* One place to modify the configuration of the entire toolchain
* Also includes the logging configuration

## Instructions

1. Run following command to turn the docker container up
```bash
[sudo] docker compose up -d 
```
2. To login into the docker container use the following command
```bash
[sudo] docker exec -it vuln_finder /bin/bash
```
The code files are present in the `/mnt/Tool` directory and the data files present in the `/mnt/Data` directory inside the container.These directories are mounted from the local folder `Data` and `Tool` folder

3. Incase of using the tool for first time run the following command to retrieve the information from FDA site
```
./FDA_Scraper.py
```

4. Run the model.py using the following command
```
./Model.py
```
5. The analysed Data will be available in the `Data/Analysed_Data.csv` file

6. The Summary Documents reside in the `Data/Summary_docs` directory

7. Resources gathered from internet such as research papers, articles are placed in `Information` directory

8. `Data/Downloads` directory is used for selenium downloads

9. For the Linux users run the following command before creating the container. Refer to this [issue](https://github.com/moby/moby/issues/2259) for more info (Not yet fixed since there is different issue with the downloading process)
```sh
sudo chown 1200:1201 Data/Downloads
```

## Output Format

* Currently the model returns the output in csv file format.
* Details of the device along with each level's result from the tool is available in the csv
* Towards end of each row the rejected papers are also listed incase to cross verify the rejected papers

## Common Errors

1. Docker should be installed properly. Please donot install docker using snap package manager. Use the following link to install docker.
* [Docker Engine Installation](https://docs.docker.com/engine/install/)
* [Docker Desktop Installation](https://docs.docker.com/desktop/install/linux-install/) (GUI version of the same)

2. Incase of inssufficient storage for library installations please rebuild the docker image
3. If issue persist reinstall docker

Uninstallation of Docker completely for a fresh install
```bash
sudo apt purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras docker.io docker-compose docker-compose-v2 docker-doc podman-docker
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /var/lib/docker /etc/docker
sudo rm /etc/apparmor.d/docker
sudo groupdel docker
sudo rm -rf /var/run/docker.sock
sudo rm -rf /usr/bin/docker-compose
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

## Reports
1. [Spreadsheet](https://docs.google.com/spreadsheets/d/1iZH7OXT8I1ZJjAsjBBCESvQfvd9mEFlEnaGs2CyKfu4/edit#gid=0) with the output of the model 
2. [Document/Report](https://docs.google.com/spreadsheets/d/1iZH7OXT8I1ZJjAsjBBCESvQfvd9mEFlEnaGs2CyKfu4/edit#gid=0) for the project 
3. [MidTerm Presentation](https://www.canva.com/design/DAF5RR5yco8/mj_s3aSHCFTOBGb5gpK7qw/edit?utm_content=DAF5RR5yco8&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton) for the project
4. [Workshop Presentation](https://docs.google.com/presentation/d/1d9Lylinp2yGWEb2P0mtAOlWBCaNNXopvOgFcHZO35BY/edit#slide=id.g2097275302c_0_280) for the project