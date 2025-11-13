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

    df.to_csv('output.csv', sep=';', index=False, encoding='utf-8')

    
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
    """Find the parent issue of a given article node."""
    # First check if root itself is the issue
    if root.tag == '{http://pkp.sfu.ca}issue':
        # Check if this article is in this issue's articles
        articles_container = root.find('.//{http://pkp.sfu.ca}articles')
        if articles_container is not None:
            for article in articles_container.findall('{http://pkp.sfu.ca}article'):
                if article == article_node:
                    return root
    
    # Otherwise search through all issues
    for issue in root.findall('.//{http://pkp.sfu.ca}issue'):
        articles_container = issue.find('{http://pkp.sfu.ca}articles')
        if articles_container is not None:
            for article in articles_container.findall('{http://pkp.sfu.ca}article'):
                if article == article_node:
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


# In[8]:


def get_article_info(article_node, root, article_id):
    
    #placeholder value
    vol = '1'
    
    base64_file = extract_base64(article_node)
    
    publications = article_node.findall('{http://pkp.sfu.ca}publication')
    publication = publications[0]
    
    # Safe locale extraction with fallback
    locale = publication.attrib.get('locale', 'en_US')
    
    # Safe attribute extraction
    publication_date = publication.attrib.get('date_published', '')
    section_reference = publication.attrib.get('section_ref', '')
    
    keywords = get_keywords(publication.find('{http://pkp.sfu.ca}keywords'))
    
    # Initialize doi before loop
    doi = ''
    for id_node in publication.findall('{http://pkp.sfu.ca}id'):
        if id_node.get('type') == 'doi':
            doi = id_node.text
    
    # Initialize title with fallback logic
    title = ''
    for title_node in publication.findall('{http://pkp.sfu.ca}title'):
        node_locale = title_node.get('locale')
        if node_locale == locale:
            title = title_node.text
            title = html.unescape(title)
            break
    
    # If no title found for the locale, get the first available title
    if not title:
        title_nodes = publication.findall('{http://pkp.sfu.ca}title')
        if title_nodes:
            title = title_nodes[0].text
            title = html.unescape(title)
    
    # Initialize abstract with fallback logic
    abstract = ''
    for abstract_node in publication.findall('{http://pkp.sfu.ca}abstract'):
        node_locale = abstract_node.get('locale')
        if node_locale == locale:
            abstract = abstract_node.text
            break
    
    # If no abstract found for the locale, get the first available abstract
    if not abstract:
        abstract_nodes = publication.findall('{http://pkp.sfu.ca}abstract')
        if abstract_nodes:
            abstract = abstract_nodes[0].text
    
    try:
        page_number = publication.findall('{http://pkp.sfu.ca}pages')[0].text
    except IndexError:
        page_number = ''

        
    author_list = publication.findall('.//{http://pkp.sfu.ca}author')
    authors = []
    for a in author_list:
        first_name_node = a.find('{http://pkp.sfu.ca}givenname')
        last_name_node = a.find('{http://pkp.sfu.ca}familyname')
        
        # Handle missing author names
        first_name = first_name_node.text if first_name_node is not None else ''
        last_name = last_name_node.text if last_name_node is not None else ''
        
        country_node = a.find('{http://pkp.sfu.ca}country')
        country = country_node.text if country_node is not None else ''
        
        email_node = a.find('{http://pkp.sfu.ca}email')
        email = email_node.text if email_node is not None else ''
            
        affiliation_node = a.find('{http://pkp.sfu.ca}affiliation')
        affiliation = affiliation_node.text if affiliation_node is not None else ''
            
        authors.append(Author(first_name, last_name, country, affiliation, email))
        
    parent_issue = find_parent_issue(article_node, root)
    issue_identification = parent_issue.find('{http://pkp.sfu.ca}issue_identification')
    
    issue_node = issue_identification.find('{http://pkp.sfu.ca}number')
    issue = issue_node.text if issue_node is not None else ''
    
    year_node = issue_identification.find('{http://pkp.sfu.ca}year')
    if year_node is not None:
        year = year_node.text
    else:
        year = publication_date[:4] if len(publication_date) >= 4 else ''
    
    # Initialize publication with fallback logic
    publication = ''
    for publication_node in issue_identification.findall('{http://pkp.sfu.ca}title'):
        node_locale = publication_node.get('locale')
        if node_locale == locale:
            publication = publication_node.text
            break
    
    # If no publication found for the locale, get the first available title
    if not publication:
        publication_nodes = issue_identification.findall('{http://pkp.sfu.ca}title')
        if publication_nodes:
            publication = publication_nodes[0].text
            
    section_information = parent_issue.find('{http://pkp.sfu.ca}sections')
    
    # Initialize section variables
    section_title = ''
    section_policy = 'no section policy'
    
    if section_information is not None:
        for section_node in section_information.findall('{http://pkp.sfu.ca}section'):
            if section_node.get('ref') == section_reference:
                # Find section title with fallback
                for section_title_node in section_node.findall('{http://pkp.sfu.ca}title'):
                    node_locale = section_title_node.get('locale')
                    if node_locale == locale:
                        section_title = section_title_node.text
                        break
                
                # If no section title found for the locale, get the first available
                if not section_title:
                    section_title_nodes = section_node.findall('{http://pkp.sfu.ca}title')
                    if section_title_nodes:
                        section_title = section_title_nodes[0].text
                
                # Find section policy with fallback
                section_policy_found = False
                for section_policy_node in section_node.findall('{http://pkp.sfu.ca}policy'):
                    node_locale = section_policy_node.get('locale')
                    if node_locale == locale:
                        section_policy = section_policy_node.text
                        section_policy_found = True
                        break
                
                # If no section policy found for the locale, get the first available
                if not section_policy_found:
                    section_policy_nodes = section_node.findall('{http://pkp.sfu.ca}policy')
                    if section_policy_nodes:
                        section_policy = section_policy_nodes[0].text
                    else:
                        section_policy = 'no section policy'
                        
                break  # Found the matching section, exit loop
                    
    return Article(article_id, 
                 title, 
                 publication, 
                 abstract, 
                 base64_file, 
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

