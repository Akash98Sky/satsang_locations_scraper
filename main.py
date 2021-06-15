from typing import Any, Dict, List
from bs4.element import ResultSet
from bs4 import BeautifulSoup
import json
import os
import requests

base_url = 'https://www.satsang.org.in'


def write_file(file_name: str, content: Any):
    file_path = './dumps/'+file_name

    if(os.path.exists('/'.join(file_path.split('/')[0:-1])) == False):
        os.makedirs('/'.join(file_path.split('/')[0:-1]))

    file = open(file_path, 'w')

    file.write(json.dumps(content, indent='\t'))

    # print('Written ' + file.name)
    file.close()


def parse_dist_kendras(contents: List):
    kendra = {'name': contents[0].text.strip() }

    for i in range(1, len(contents)):
        if contents[i].text.strip() == 'Account:':
            kendra['account'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Established:':
            kendra['estd'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'History / Description:':
            kendra['history'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Address:':
            kendra['address'] = ''
            for string in contents[i+1].strings:
                kendra['address'] = kendra['address'] + string.replace('  ', '').replace('\n', '') + '\n'
        elif contents[i].text.strip() == 'Contact No:':
            kendra['contact'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Nearest Railway Station/Bus Stand/Airport:':
            kendra['near'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Details:':
            kendra['details'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Worker In-charge with Contact No.:':
            kendra['worker_contact'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Other workers with Contact No.:':
            kendra['other_workers_contact'] = contents[i+1].text.strip()
        elif contents[i].text.strip() == 'Contact No:':
            kendra['contact'] = contents[i+1].text.strip()
        elif contents[i].get('style') == 'clear:both; float:left; color:#CCCCCC;':
            kendra['abbreviations'] = contents[i].text.strip()
    
    return kendra


def scrape_dist_page(dists_json: List[Dict[str, Any]], state:Dict[str, Any]):
    for dist in dists_json:
        id=str(dist['id'])
        name=dist['name']

        dist_page = requests.get(base_url + '/index.php?p=locator&state=' + state['id'] + '&dist=' + id)

        if (dist_page.status_code == 200):
            soup = BeautifulSoup(dist_page.content, 'html.parser')

            inner_contents = soup.select('div.inner > div > div')
            content_started = False
            single_content = []
            kendra_content_list = []

            for inner in inner_contents:
                if(content_started):
                    try:
                        if(inner['style'] == 'clear:both;  width:100%; border-bottom:1px solid #333333;'):
                            kendra = parse_dist_kendras(single_content)
                            kendra_content_list.append(kendra)
                            single_content = []
                        elif(inner.text.strip() != '&nbsp;'):
                            single_content.append(inner)
                    except:
                        pass

                elif(inner.find('form', {'name': 'f2'}) != None):
                    content_started=True

            print('DISTRICT :: Success ', id+'-'+name)
            write_file(state['id']+'-'+state['name']+'/'+id+'-'+name+'.json' ,kendra_content_list)
        else:
            print('DISTRICT :: Fail ', id+'-'+name)


def main():
    page = requests.get(base_url + '/index.php?p=locator')

    if(page.status_code == 200):
        soup = BeautifulSoup(page.content, 'html.parser')
        states = soup.select('select')[0].select('option')[1:]
        state_json: List[Dict[str, Any]] = []
        for state in states:
            state_json.append({
                "id": state.get('value'),
                "name": state.text.strip()
            })

        write_file('states.json', state_json)

        for state in state_json:
            id = state['id']
            state_dists_page = requests.get(base_url + '/index.php?p=locator&state=' + id)

            if(page.status_code == 200):
                soup = BeautifulSoup(state_dists_page.content, 'html.parser')

                dists: ResultSet = soup.select(
                    'select')[1].select('option')[1:]

                dists_json: List[Dict[str, Any]] = []
                for dist in dists:
                    dists_json.append({
                        "id": int(dist.get('value')),
                        "name": dist.text.strip()
                    })

                dist_file_name = state['id'] + '-' + state['name'] + '/' + 'districts.json'
                write_file(dist_file_name, dists_json)
                scrape_dist_page(dists_json, state)

                print('STATE :: Success ', state['id']+'-'+state['name'])
            else:
                print('STATE :: Failed ', state['id']+'-'+state['name'])

            print()


if __name__ == '__main__':
    print(' ===========================================')
    print('|| SATSANG Kendra/Mandir Locations Scraper ||')
    print(' ===========================================')

    main()

    # ## Debugging
    # scrape_dist_page([{
	# 	"id": 166,
	# 	"name": "FARIDABAD"
	# }], {
	# 	"id": "13",
	# 	"name": "Haryana"
	# })
