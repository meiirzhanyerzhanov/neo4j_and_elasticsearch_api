import py2neo
from py2neo import Graph
from py2neo import Node, Relationship
import pandas as pd
from py2neo.database import ClientError
from elasticsearch import Elasticsearch


def get_correct_data(data):
    if str(data) != 'nan':
        return data
    else:
        return ""


graph = Graph("http://neo4j:7474/db/data/", user="neo4j", password="test")
es = Elasticsearch('http://elasticsearch:9200')


def build_db():
    try:
        graph.run('CREATE CONSTRAINT ON (w:Person) ASSERT w.id IS UNIQUE;')
        graph.run('CREATE CONSTRAINT ON (w:Organization) ASSERT w.group_id IS UNIQUE;')
    except:
        print("Constraint already exist")

    df = pd.read_csv('gb_parliament.csv')

    all_organization = set()

    for group_id in df['group_id']:
        all_organization.add(group_id)

    for group_id in all_organization:
        if not graph.run("MATCH (n:Organization {group_id: '" + group_id + "'}) RETURN n").data():
            organization = Node("Organization",
                                name=get_correct_data(list(df.loc[df['group_id'] == str(group_id)]['group'])[0]),
                                group_id=get_correct_data(group_id))
            graph.create(organization)
            doc = {
                'name': get_correct_data(list(df.loc[df['group_id'] == str(group_id)]['group'])[0]),
            }
            res = es.index(index="organization", id=get_correct_data(group_id), body=doc)

    for i in range(len(df['id'])):
        if not graph.run("MATCH (n:Person {id: '" + df['id'][i] + "'}) RETURN n").data():
            person = Node("Person", id=get_correct_data(df['id'][i]), name=get_correct_data(df['name'][i]),
                          alias=get_correct_data(df['sort_name'][i]), email=get_correct_data(df['email'][i]),
                          nationality='GB')
            membership = Relationship(person, "Members of", graph.run(
                "MATCH (n:Organization {group_id: '" + df['group_id'][i] + "'}) RETURN n").data()[0]['n'])
            print("ADD")
            graph.create(person)
            graph.create(membership)
            doc = {
                'name': get_correct_data(df['name'][i]),
                'alias': get_correct_data(df['sort_name'][i]),
                'email': get_correct_data(df['email'][i]),
                'nationality': "GB",
            }
            res = es.index(index="person", id=get_correct_data(df['id'][i]), body=doc)
