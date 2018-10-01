## jgi_eukarya_scraping

from selenium import webdriver
import time
import os
import re
import json
from bs4 import BeautifulSoup        

def activate_driver():
    """
    Activate chrome driver used to automate webpage navigation (see: https://sites.google.com/a/chromium.org/chromedriver/)
    The chrome driver .exec file must be in the home directory

    returns: driver [object]
    """
    homedir = os.path.expanduser('~')
    return webdriver.Chrome(homedir+'/chromedriver')

def get_domains_url_from_jgi_img_homepage(driver,homepage_url,domain,database='jgi'):
    """
    load homepage_url -> retrieve domain's url

    driver: the chrome driver object
    homepage_url: url of the jgi homepage. should be 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi' as of 6/15/2017
    database: choose to use only the jgi database, or all database [default=jgi]
    """
    if domain=='eukarya':
        domain_str = 'Eukaryota'
    elif domain=='bacteria':
        domain_str = 'Bacteria'
    elif domain=='archaea':
        domain_str = 'Archaea'
    # elif domain=='metagenomes':
    #     domain_str = '*Microbiome'
    else:
        raise ValueError("Domain must be one of: eukarya, bacteria, archaea")#, or metagenomes")

    driver.get(homepage_url)
    time.sleep(5)
    htmlSource = driver.page_source

    ## All ampersands (&) must be followed by 'amp;'
    if database == 'jgi':
        regex = r'href=\"main\.cgi(\?section=TaxonList&amp;page=taxonListAlpha&amp;domain={0}&amp;seq_center=jgi)\"'.format(domain_str)
    elif database == 'all':
        regex = r'href=\"main\.cgi(\?section=TaxonList&amp;page=taxonListAlpha&amp;domain={0})\"'.format(domain_str)
    else:
        raise ValueError("Database must be 'jgi' or 'all'")

    ## All bacteria html not present on jgi homepage
    if domain=='bacteria' and database=='all':
        raise Warning("This is unstable and unreliable at the moment.")
        return "https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TaxonList&page=taxonListAlpha&domain=Bacteria"

    else:
        match = re.search(regex, htmlSource)
        suffix = match.group(1)
        domain_url = homepage_url+suffix

        return domain_url

def get_domain_json_from_domain_url(driver,domain_url):
    """
    load domain_url- > retrieve domain_json_url -> load domain_json_url -> retrieve domain_json
    
    driver: the chrome driver object
    domain_url: url of domain database
    """

    driver.get(domain_url)
    time.sleep(5) ## This value might need to be increased to 60 seconds if domain==bacteria and database==all
    htmlSource = driver.page_source
    # driver.quit()

    regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
    match = re.search(regex, htmlSource)
    domain_json_suffix = match.group(1)
    domain_url_prefix = domain_url.split('main.cgi')[0]
    domain_json_url = domain_url_prefix+domain_json_suffix

    driver.get(domain_json_url)
    time.sleep(5)
    # jsonSource = driver.page_source

    ## convert the jsonSource into a dict of dicts here
    domain_json = json.loads(driver.find_element_by_tag_name('body').text)

    return domain_json


def get_organism_urls_from_domain_json(driver,homepage_url,domain_json):
    """
    parse domain_json -> retrieve organism_urls

    driver: the chrome driver object
    homepage_url: url of the jgi homepage. should be 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi' as of 6/15/2017
    domain_json: json text of domain
    """

    all_GenomeNameSampleNameDisp =  [d['GenomeNameSampleNameDisp'] for d in domain_json['records']]

    organism_urls = list()

    for htmlandjunk in all_GenomeNameSampleNameDisp:
        regex = r"<a href='main\.cgi(.*)'>"
        match = re.search(regex, htmlandjunk)
        html_suffix = match.group(1)
        full_url = homepage_url+html_suffix
        organism_urls.append(full_url)

    return organism_urls

#######

def get_organism_htmlSource_and_metadata(driver, organism_url):
    """
    load organism_url -> retrieve organism_htmlSource & metadata

    driver: the chrome driver object
    organism_url: url for an single organism
    """

    driver.get(organism_url)
    time.sleep(5)
    organism_htmlSource = driver.page_source

    metadata_table_dict = get_organism_metadata_while_on_organism_page(organism_htmlSource)

    return organism_htmlSource, metadata_table_dict


def get_enzyme_url_from_organism_url(organism_url, organism_htmlSource):

    """
    organism_htmlSource -> parse out enzyme_url

    driver: the chrome driver object
    organism_url: url for an single organism
    """

    
    regex = r'<a href=\"(main\.cgi\?section=TaxonDetail&amp;page=enzymes&amp;taxon_oid=\d*)\"'
    match = re.search(regex, organism_htmlSource)

    print "Getting enzyme_url from organism url: %s"%(organism_url)

    enzyme_url_suffix = match.group(1)
    enzyme_url_prefix = organism_url.split('main.cgi')[0]
    enzyme_url = enzyme_url_prefix+enzyme_url_suffix    

    return enzyme_url

## I think this metadata is in the json
def get_organism_metadata_while_on_organism_page(htmlSource):
    """
    htmlSource -> dictionary of organism metadata

    htmlSource: the organism_url driver's .page_source
    """

    # return dict of metagenome table data
    bs = BeautifulSoup(htmlSource,"html.parser")
    metadata_table = bs.findAll('table')[0]

    metadata_table_dict = dict()
    for row in metadata_table.findAll('tr'):

        if (len(row.findAll('th')) == 1) and (len(row.findAll('td')) == 1):

            row_key = row.findAll('th')[0].text.rstrip()
            row_value = row.findAll('td')[0].text.rstrip() if row.findAll('td')[0] else None
            metadata_table_dict[row_key] = row_value

    metadata_table_dict.pop('Project Geographical Map', None)

    ## metadata_table_dict['Taxon Object ID'] should be the way we identify a metagenome

    return metadata_table_dict

def get_enzyme_json_from_enzyme_url(driver,enzyme_url):
    """
    load enzyme_url -> retrieve enzyme_json_url -> load enzyme_json_url -> retrieve enzyme_json

    driver: the chrome driver object
    enzyme_url: url for an single enzyme type from an single organism
    """

    driver.get(enzyme_url)
    time.sleep(5)
    htmlSource = driver.page_source
    # driver.quit()

    regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
    match = re.search(regex, htmlSource)
    enzyme_json_suffix = match.group(1)
    enzyme_url_prefix = enzyme_url.split('main.cgi')[0]
    enzyme_json_url = enzyme_url_prefix+enzyme_json_suffix

    driver.get(enzyme_json_url)
    time.sleep(5)
    # jsonSource = driver.page_source

    ## convert the jsonSource into a dict of dicts here
    enzyme_json = json.loads(driver.find_element_by_tag_name('body').text)

    return enzyme_json

# def parse_enzyme_info_from_enzyme_json(enzyme_json):

#     enzyme_dict = dict() # Dictionary of ec:[enzymeName,genecount] for all ecs in a single metagenome

#     for i, singleEnzymeDict in enumerate(enzyme_json['records']):
#         ec = singleEnzymeDict['EnzymeID']
#         enzymeName = singleEnzymeDict['EnzymeName']
#         genecount = singleEnzymeDict['GeneCount']

#         enzyme_dict[ec] = [enzymeName,genecount]

#     return enzyme_dict

###############################################################
## get URLs for pH specific scraping
###############################################################
def load_json(fname):
    """
    Wrapper to load json in single line

    :param fname: the filepath to the json file
    """
    with open(fname) as f:
        return json.load(f)

## Tested and works
def check_overlap_number(range_1,i):
    if (i>=min(range_1)) and (i<=max(range_1)):
        return True
    else:
        return False

## Tested and works
def check_overlap_ranges(range_1,range_2):
    # order the ranges so that the range with the smallest min is first
    # check if the min of range2 is less than the max of range 1
    ranges = [range_1,range_2]
    if min(range_2)<min(range_1):
        ranges = ranges[::-1]
    if min(ranges[1])<=max(ranges[0]):
        return True
    else:
        return False

def get_entries_within_ph_range(records, desired_ph_range):
    entries_with_phs_in_range = list()
    for entry in records:
        in_desired_ph_range = False
        ph_range_str = entry['pH'].split('-')

        if len(ph_range_str) == 1:
            try:
                ph = float(ph_range_str[0])
                in_desired_ph_range = check_overlap_number(desired_ph_range,ph)

            except:
                pass
        elif len(ph_range_str) == 2:
            try:
                ph_min = float(ph_range_str[0])
                ph_max = float(ph_range_str[1])
                ph = (ph_min,ph_max)
                in_desired_ph_range = check_overlap_ranges(desired_ph_range,ph)
            except:
                pass
        
        if in_desired_ph_range == True:
            entries_with_phs_in_range.append(entry)
    
    return entries_with_phs_in_range

def format_urls_for_scraping(homepage_url,entries_with_phs_in_range):
    all_GenomeNameSampleNameDisp =  [d['GenomeNameSampleNameDisp'] for d in entries_with_phs_in_range]

    organism_urls = list()

    for htmlandjunk in all_GenomeNameSampleNameDisp:
        regex = r"<a href='main\.cgi(.*)'>"
        match = re.search(regex, htmlandjunk)
        html_suffix = match.group(1)
        full_url = homepage_url+html_suffix
        organism_urls.append(full_url)

    return organism_urls

def main():

    driver = activate_driver()
    homepage_url = 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi'
    domain = 'bacteria'
    database = 'all'
    save_dir = 'jgi/2018-09-29/ph_jsons/%s/'%domain

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    jgi_eukarya = list()

    print "Scraping all %s genomes ..."%domain

    ## Get all urls from the domain
    # domain_url = get_domains_url_from_jgi_img_homepage(driver,homepage_url,domain,database=database)
    # domain_json = get_domain_json_from_domain_url(driver,domain_url)
    # organism_urls = get_organism_urls_from_domain_json(driver,homepage_url,domain_json)

    ## Get pH specific urls from the domain
    if domain=='archaea':
        metadata = load_json("jgi/metadata/archaea_metadata.json")
    elif domain=='bacteria':
        metadata = load_json("jgi/metadata/bacteria_metadata_subset.json")
    elif domain=='eukarya':
        raise Warning("Eukarya do not have any organisms in range currently")
        metadata = load_json("jgi/metadata/eukarya_metadata.json")

    records = metadata['records']
    ph_range = (9.0,11.0)
    entries_with_phs_in_range = get_entries_within_ph_range(records,ph_range)
    organism_urls = format_urls_for_scraping(homepage_url,entries_with_phs_in_range)

    ## 
    for organism_url in organism_urls:

        print "Scraping %s: %s ..."%(domain,organism_url)
        organism_htmlSource,metadata_table_dict = get_organism_htmlSource_and_metadata(driver, organism_url)

        # single_organism_dict = {'metadata':metadata_table_dict}
        taxon_id = metadata_table_dict['Taxon ID']
        enzyme_url = get_enzyme_url_from_organism_url(organism_url, organism_htmlSource)
        enzyme_json = get_enzyme_json_from_enzyme_url(driver,enzyme_url)

        # enzyme_dict = parse_enzyme_info_from_enzyme_json(enzyme_json)
        # single_organism_dict['genome'] = enzyme_dict

        jgi_eukarya.append(enzyme_json)

        with open(save_dir+taxon_id+'.json', 'w') as outfile:
    
            json.dump(enzyme_json,outfile)

        print "Done scraping %s."%domain
        print "-"*80

    print "Done scraping %s."%domain
    print "="*90



    print "Writing json to file..."

    combined_json_fname = 'jgi/2018-09-29/ph_jsons/jgi_ph_%s.json'%domain
    with open(combined_json_fname, 'w') as outfile:
        
        json.dump(jgi_eukarya,outfile)

    print "Done."

    ## Can i write it so that it scrapes many at a time?

if __name__ == '__main__':
    main()



