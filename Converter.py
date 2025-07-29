#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import sys
import xml.etree.ElementTree as ET
import html


# In[3]:


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <xml_file>")
        sys.exit(1)  # Exit with an error code

    # Retrieve the XML file from command-line arguments
    xml_file = sys.argv[1]
    
    # Open the XML file with the correct encoding
    with open(xml_file, 'rb') as file:
        # Parse the XML file
        tree = ET.parse(file)
        root = tree.getroot()
    
    articles = root.findall('.//{http://pkp.sfu.ca}article')
    
    rows = []
    row_id = 0
    
    for article in articles:
        #print(row_id)
        processed = get_article_info(article, root, row_id)
        df = pd.DataFrame.from_dict(processed.to_row())
        rows.append(df)
        row_id += 1
        
    df = pd.concat(rows)
    
    df = df.fillna('')
    
    df['section_policy'] = df['section_policy'].replace('', 'no section policy').fillna('no section policy')
    
    df = df.rename(columns={"article_id": "id"})
    
    df['volume'] = df['volume'].astype(str)
    
    
    df['issue'] = df['issue'].astype(str)

    filename = xml_file.removesuffix('.xml')

    df.to_csv(f'{filename}.csv', sep=';', index=False, encoding='utf-8')

    
    return df


# In[4]:


def extract_base64(article_node):
    # Find all submission files in the article node
    submission_files = article_node.findall('{http://pkp.sfu.ca}submission_file')

    # Iterate through each submission file
    for submission in submission_files:
        # Check each file inside the submission file
        for file in submission.findall('{http://pkp.sfu.ca}file'):
            # Check if the genre is 'Manuscript'
            if submission.get('genre') == 'Manuscript':
                # Find the <embed> tag that contains the base64 content
                embed = file.find('{http://pkp.sfu.ca}embed')
                if embed is not None:
                    # Add the base64 content to the list
                    base64_contents = embed.text
                    
    return base64_contents


# In[3]:


def extract_tile(article_node):
    #find all covers
    cover = article_node.find('.//{http://pkp.sfu.ca}cover')
    
    output = """
    iVBORw0KGgoAAAANSUhEUgAAAEsAAABLCAIAAAC3LO29AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA4ZpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMDE0IDc5LjE1Njc5NywgMjAxNC8wOC8yMC0wOTo1MzowMiAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpjNTdlODNiOC02MmM4LTRhMDUtYWMxMi1iMmRlNWMyNDA0ZGMiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6MDBFMkU5RjJGOEUyMTFFNTlFODFCQkZCQ0I1REQwREQiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MDBFMkU5RjFGOEUyMTFFNTlFODFCQkZCQ0I1REQwREQiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTQgKE1hY2ludG9zaCkiPiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDpiODYyY2RmMC0wNWViLTQwMTEtOGRkNC0xODMzYzMzODU2NWIiIHN0UmVmOmRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDo5YWNjYTc5Zi01YmY4LTExNzgtOWY0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
    """
    
    print(cover)
    if cover is not None:
        embed = cover.find('{http://pkp.sfu.ca}embed')
        if embed is not None:
            #add the base64 content
            output = embed.text
    
    return output


# In[5]:


class Author:
    def __init__(self, first_name, last_name, country, affiliation, email):
        self.first_name = first_name
        self.last_name = last_name
        self.country = country
        self.affiliation = affiliation
        self.email = email


# In[6]:


class Article:
    def __init__(self, 
                 article_id, 
                 title, 
                 publication, 
                 abstract, 
                 base64_file, 
                 tile,
                 publication_date, 
                 year, 
                 vol,
                 issue, 
                 page_number, 
                 section_title,
                 section_policy,
                 section_reference,
                 doi,
                 authors, 
                 locale,
                 keywords):
        
        self.article_id = article_id
        self.title = title
        self.publication = publication
        self.abstract = abstract
        self.base64_file = base64_file
        self.tile = tile
        self.publication_date = publication_date
        self.year = year
        self.vol = vol
        self.issue = issue
        self.page_number = page_number
        self.section_title = section_title
        self.section_policy = section_policy
        self.section_reference = section_reference
        self.doi = doi
        self.authors = authors
        self.locale = locale
        self.keywords = keywords
    
    def export_authors(self):
        #generate a dict with authors and column titles
        amount_of_authors = len(self.authors)
        author_id = 0
        output = {}
        for a in self.authors:
            first_name_column = 'author_given_name_' + str(author_id)
            last_name_column = 'author_family_name_' + str(author_id)
            affiliation_column = 'author_affiliation_' + str(author_id)
            country_column = 'author_country_' + str(author_id)
            email_column = 'author_email_' + str(author_id)
            output[first_name_column] = [a.first_name]
            output[last_name_column] = [a.last_name]
            output[affiliation_column] = [a.affiliation]
            output[country_column] = [a.country]
            output[email_column] = [a.email]
            author_id += 1
        
        return output
    
    def to_row(self):
        #function that outputs the article as a single row for a df, as a list
        output = {'article_id': [self.article_id],
                 'title': [self.title],
                 'publication': [self.publication],
                'abstract': [self.abstract],
                'file': [self.base64_file],
                'tile': [self.tile],
                'publication_date': [self.publication_date],
                'year': [self.year],
                'volume': [self.vol],
                'issue': [self.issue],
                'page_number': [self.page_number],
                'section_title': [self.section_title],
                'section_policy': [self.section_policy],
                'section_reference': [self.section_reference],
                'doi': [self.doi],
                 'keywords': [self.keywords]}
        
        authors = self.export_authors()
        
        output = output | authors
        
        return output


# In[7]:


# Function to find the parent issue of a given article node
def find_parent_issue(article_node, root):
    for issue in root.findall('.//{http://pkp.sfu.ca}issue'):  # Iterate through all issues
        if article_node in issue.findall('.//{http://pkp.sfu.ca}article'):  # Check if the article is in this issue
            return issue
    return None


# In[ ]:


def get_keywords(keywords_node):
    output = []
    for keyword in keywords_node.findall('.//{http://pkp.sfu.ca}keyword'):
        output.append(keyword.text)
    
    output_string = ''
    first = False
    for keyword in output:
        if first:
            output_string = output_string + '[;sep;]' + keyword  
        else:
            output_string = output_string + keyword
            first = True
    
    return output_string


# In[2]:


def get_article_info(article_node, root, article_id):
    
    #placeholder value
    vol = '1'
    
    base64_file = extract_base64(article_node)
    tile = extract_tile(article_node)
    publications = article_node.findall('{http://pkp.sfu.ca}publication')
    publication = publications[0]
    
    locale = publication.attrib['locale']
    publication_date = publication.attrib['date_published']
    section_reference = publication.attrib['section_ref']
    
    keywords = get_keywords(publication.find('{http://pkp.sfu.ca}keywords'))
    
    for id_node in publication.findall('{http://pkp.sfu.ca}id'):
        if id_node.get('type') == 'doi':  # Check for the 'type' attribute
            doi = id_node.text
    
    for title_node in publication.findall('{http://pkp.sfu.ca}title'):
        if title_node.get('locale') == locale:
            title = title_node.text
            title = html.unescape(title)
    
    for abstract_node in publication.findall('{http://pkp.sfu.ca}abstract'):
        if abstract_node.get('locale') == locale:
            abstract = abstract_node.text
    
    try:
        page_number = publication.findall('{http://pkp.sfu.ca}pages')[0].text
    except IndexError:
        page_number = ' '

        
    author_list = publication.findall('.//{http://pkp.sfu.ca}author')
    authors = []
    for a in author_list:
        first_name = a.find('{http://pkp.sfu.ca}givenname').text
        last_name = a.find('{http://pkp.sfu.ca}familyname').text
        
        try:
            country = a.find('{http://pkp.sfu.ca}country').text
        except AttributeError:
            country = ''
        
        try:
            email = a.find('{http://pkp.sfu.ca}email').text
        except AttributeError:
            email = ''
            
        try:    
            affiliation = a.find('{http://pkp.sfu.ca}affiliation').text
        except AttributeError:
            affiliation = ''
            
        authors.append(Author(first_name, last_name, country, affiliation, email))
        
    parent_issue = find_parent_issue(article_node, root)
    issue_identification = parent_issue.find('{http://pkp.sfu.ca}issue_identification')
    
    issue = issue_identification.find('{http://pkp.sfu.ca}number').text
    
    try:
        year = issue_identification.find('{http://pkp.sfu.ca}year').text
    except AttributeError:
        year = publication_date[:4]
    
    for publication_node in issue_identification.findall('{http://pkp.sfu.ca}title'):
        if publication_node.get('locale') == locale:
            publication = publication_node.text
            
    section_information = parent_issue.find('{http://pkp.sfu.ca}sections')
    for section_node in section_information.findall('{http://pkp.sfu.ca}section'):
        if section_node.get('ref') == section_reference:
            for section_title_node in section_node.findall('{http://pkp.sfu.ca}title'):
                if section_title_node.get('locale') == locale:
                    section_title = section_title_node.text
            
            section_policy = ""
            for section_policy_node in section_node.findall('{http://pkp.sfu.ca}policy'):
                if section_policy_node.get('locale') == locale:
                    section_policy = section_policy_node.text
                    
                else:
                    section_policy = 'no section policy'
                    
    return Article(article_id, 
                 title, 
                 publication, 
                 abstract, 
                 base64_file, 
                 tile,
                 publication_date,
                 year, 
                 vol,  
                 issue, 
                 page_number, 
                 section_title,
                 section_policy,
                 section_reference,
                 doi,
                 authors, 
                 locale,
                 keywords)


# In[9]:


if __name__ == "__main__":
    main()

