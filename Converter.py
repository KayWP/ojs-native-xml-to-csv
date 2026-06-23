#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import sys
import xml.etree.ElementTree as ET
import html


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


def extract_base64(article_node):
    # Find all submission files in the article node
    submission_files = article_node.findall('{http://pkp.sfu.ca}submission_file')

    # Iterate through each submission file
    for submission in submission_files:
        # Check each file inside the submission file
        for file in submission.findall('{http://pkp.sfu.ca}file'):
            # Check if the genre is 'Manuscript' AND the extension is 'pdf'
            if submission.get('genre') == 'Manuscript' and file.get('extension') == 'pdf':
                # Find the <embed> tag that contains the base64 content
                embed = file.find('{http://pkp.sfu.ca}embed')
                if embed is not None and embed.text:
                    # Return the base64 content
                    return embed.text
    
    # Return empty string if no PDF manuscript found
    return ''


class Author:
    def __init__(self, first_name, last_name, country, affiliation, email):
        self.first_name = first_name
        self.last_name = last_name
        self.country = country
        self.affiliation = affiliation
        self.email = email


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
        # Generate a dict with authors and column titles
        output = {}
        for author_id, a in enumerate(self.authors):
            first_name_column = f'author_given_name_{author_id}'
            last_name_column = f'author_family_name_{author_id}'
            affiliation_column = f'author_affiliation_{author_id}'
            country_column = f'author_country_{author_id}'
            email_column = f'author_email_{author_id}'
            output[first_name_column] = [a.first_name]
            output[last_name_column] = [a.last_name]
            output[affiliation_column] = [a.affiliation]
            output[country_column] = [a.country]
            output[email_column] = [a.email]
        
        return output
    
    def to_row(self):
        # Function that outputs the article as a single row for a df, as a dict
        output = {
            'article_id': [self.article_id],
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
            'keywords': [self.keywords]
        }
        
        authors = self.export_authors()
        output = output | authors
        
        return output


def find_parent_issue(article_node, root):
    # Find the parent issue of a given article node
    for issue in root.findall('.//{http://pkp.sfu.ca}issue'):
        if article_node in issue.findall('.//{http://pkp.sfu.ca}article'):
            return issue
    return None


def get_keywords(keywords_node):
    # Check if keywords_node is None (no keywords element found)
    if keywords_node is None:
        return ''
    
    output = []
    for keyword in keywords_node.findall('.//{http://pkp.sfu.ca}keyword'):
        if keyword.text:
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


def get_article_info(article_node, root, article_id):
    # Placeholder value
    vol = '1'
    
    base64_file = extract_base64(article_node)
    publications = article_node.findall('{http://pkp.sfu.ca}publication')
    publication = publications[0]
    
    # Try to read locale from publication attribute
    locale = publication.attrib.get('locale')

    # If missing, infer from child nodes (title, abstract, etc.)
    if not locale:
        for child in publication:
            found_locale = child.attrib.get('locale')
            if found_locale:
                locale = found_locale
                break

    # If still missing, fall back to default
    if not locale:
        locale = 'en'
        
    publication_date = publication.attrib['date_published']
    section_reference = publication.attrib['section_ref']
    
    keywords = get_keywords(publication.find('{http://pkp.sfu.ca}keywords'))
    
    # Initialize variables with default values
    doi = ''
    title = ''
    abstract = ''
    
    for id_node in publication.findall('{http://pkp.sfu.ca}id'):
        if id_node.get('type') == 'doi':
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
    
    # Initialize publication with default value
    publication_title = ''
    for publication_node in issue_identification.findall('{http://pkp.sfu.ca}title'):
        if publication_node.get('locale') == locale:
            publication_title = publication_node.text
            
    section_information = parent_issue.find('{http://pkp.sfu.ca}sections')
    
    # Initialize section variables with default values
    section_title = ''
    section_policy = 'no section policy'
    
    for section_node in section_information.findall('{http://pkp.sfu.ca}section'):
        if section_node.get('ref') == section_reference:
            for section_title_node in section_node.findall('{http://pkp.sfu.ca}title'):
                if section_title_node.get('locale') == locale:
                    section_title = section_title_node.text
            
            for section_policy_node in section_node.findall('{http://pkp.sfu.ca}policy'):
                if section_policy_node.get('locale') == locale:
                    section_policy = section_policy_node.text
                    break
                    
    return Article(
        article_id, 
        title, 
        publication_title,
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
        keywords
    )


if __name__ == "__main__":
    main()