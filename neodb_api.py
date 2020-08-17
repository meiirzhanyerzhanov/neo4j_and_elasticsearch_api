from flask import Flask, jsonify, request, session
from py2neo import Graph
from py2neo import Node, Relationship
from elasticsearch import Elasticsearch
import neo4j_build
username = "neo4j"
password = "test"

app = Flask(__name__)
graph = Graph("http://neo4j:7474/db/data/", user=username, password=password)
es = Elasticsearch('http://elasticsearch:9200')

@app.route("/build")
def build_db():
    try:
        neo4j_build.build_db()
    except Exception as e:
        return jsonify(e), 500
    return "Successfully build", 200


@app.route("/persons", methods=['GET', 'POST'])
def all_persons():
    if request.method == 'GET':
        # default size
        size = 10

        # Check if amount of data to retrieve is given or not
        if 'size' in request.form:
            size = int(request.form['size'])

        # Get data from elasticsearch
        result = es.search(index="person", body={"query": {"match_all": {}}}, size=size)

        # Retrieved data to json
        result_json = {}
        for i in range(len(result['hits']['hits'])):
            result_json[i] = result['hits']['hits'][i]['_source']

        return result_json, 200
    if request.method == 'POST':

        # check if id is given or not
        if 'id' not in request.json:
            return "ID is required", 400
        id_ = request.json['id']

        # check if personal info is given
        data = dict()
        person_attr = {'name', 'alias', 'email', 'nationality', 'group', 'group_id'}
        for i in person_attr:
            if i in request.json:
                data[i] = request.json[i]
            else:
                data[i] = ""

        if not graph.run("MATCH (n:Person {id: '" + id_ + "'}) RETURN n").data():

            person = Node("Person", id=id_, name=data['name'],
                          alias=data['alias'], email=data['email'],
                          nationality=data['nationality'])
            graph.create(person)

            doc = {
                'name': data['name'],
                'alias': data['alias'],
                'email': data['email'],
                'nationality': data['nationality'],
            }
            print(es.index(index="person", id=id_, body=doc))

            if data['group_id']:
                organization = graph.run(
                    "MATCH (n:Organization {group_id: '" + data['group_id'] + "'}) RETURN n").data()

                if organization:
                    membership = Relationship(person, "Members of", graph.run(
                        "MATCH (n:Organization {group_id: '" + data['group_id'] + "'}) RETURN n").data()[0][
                        'n'])

                    graph.create(membership)
                else:
                    organization = Node("Organization", name=data['group'],
                                        group_id=data['group_id'])
                    doc = {
                        'name': data['group'],
                    }
                    print(es.index(index="organization", id=id, body=doc))
                    graph.create(organization)

                    membership = Relationship(person, "Members of", organization)
                    graph.create(membership)

            return person, 200
        else:
            return "The user already exist"


@app.route("/persons/search", methods=['GET'])
def search_person_by_name():
    query_body = {
        "query": {
            "match": {
                "name": request.args.get('name')
            }
        }
    }
    data = es.search(index='person', body=query_body)

    return jsonify(data['hits']['hits']), 200


@app.route("/persons/<string:id>", methods=['GET', 'PATCH', 'DELETE'])
def get_person_by_id(id: str):
    if request.method == 'GET':
        try:
            res = es.get(index="person", id=id)['_source']

            neo4j_data = graph.run("MATCH (n:Person {id: '"+id+"'})-[rel]->(a:Organization) RETURN a").data()

            res['group_id'] = neo4j_data[0]['a']['group_id']
            res['group_name'] = neo4j_data[0]['a']['name']

            return res, 200
        except Exception as e:
            return str(e), 404

    if request.method == 'DELETE':
        try:
            result = graph.run("MATCH (n:Person {id: '" + id + "'})-[rel]->(a:Organization) RETURN a").data()
            if result:
                graph.run("MATCH (n:Person {id: '" + id + "'})-[rel]->(a:Organization) DELETE rel, n")
            else:
                graph.run("MATCH (n:Person {id: '" + id + "'}) DELETE n")
            es.delete(index='person', id=id)
        except:
            return "Data is not exist", 404
        return "Deleted successfully", 200
    if request.method == 'PATCH':
        try:
            data = es.get(index="person", id=id)['_source']
        except:
            return "No person for id: " + id, 404
        try:
            for i in request.json:
                data[i] = request.json[i]

            graph.run("MATCH (n:Person {id: '" + id + "'}) SET n.name='" + data['name'] + "', n.alias='" + data[
                'alias'] + "', n.email='" + data['email'] + "', n.nationality='" + data['nationality'] + "'")

            es.index(index="person", id=id, body=data)

            return data, 200
        except Exception as e:
            return str(e), 400


@app.route("/organizations", methods=['GET', 'POST'])
def all_organizations():
    if request.method == 'GET':

        # default size
        size = 10

        # Check if amount of data to retrieve is given or not
        if 'size' in request.form:
            size = int(request.form['size'])

        # Get data from elasticsearch
        result = es.search(index="organization", body={"query": {"match_all": {}}}, size=size)

        # Retrieved data to json
        result_json = {}
        for i in range(len(result['hits']['hits'])):
            result_json[str(i)] = result['hits']['hits'][i]['_source']

        return result_json, 200
    if request.method == 'POST':

        # check if group_id is given or not
        if 'group_id' not in request.json:
            return "Group ID is required", 400

        group_id = request.json['group_id']
        group = ''

        if 'name' in request.json:
            group = request.json['name']

        organization = graph.run(
            "MATCH (n:Organization {group_id: '" + group_id + "'}) RETURN n").data()

        if organization:
            return "Group with group_id " + group_id + " is already exist"

        organization = Node("Organization", name=group,
                            group_id=group_id)

        graph.create(organization)

        doc = {
            'name': group,
        }
        es.index(index="organization", id=group_id, body=doc)
        return "Successfully created", 200


@app.route("/organizations/<string:id>", methods=['GET', 'PATCH', 'DELETE'])
def get_organization_by_id(id: str):
    if request.method == 'GET':
        try:
            res = es.get(index="organization", id=id)
            if res['_source']:
                return res['_source'], 200
            else:
                return "Not Found", 404
        except:
            return "Not Found", 404

    if request.method == 'DELETE':
        try:
            graph.run("MATCH (n:Person)-[rel]->(a:Organization {group_id: '" + id + "'}) Delete rel").data()
            graph.run("MATCH (a:Organization {group_id: '" + id + "'}) Delete a")

            es.delete(index="organization", id=id)
        except:
            return "Data is not exist", 404
        return "Deleted successfully", 200
    if request.method == 'PATCH':
        try:

            data = es.get(index="organization", id=id)['_source']
        except:
            return "No organization for group_id: " + id, 404
        try:
            for i in request.json:
                data[i] = request.json[i]
            print(data)
            graph.run("MATCH (n:Organization {group_id: '" + id + "'}) SET n.name='" + data['name'] + "'")

            es.index(index="organization", id=id, body=data)

            return data, 200
        except Exception as e:
            return str(e), 400


if __name__ == "__main__":
    app.run(host='0.0.0.0')
