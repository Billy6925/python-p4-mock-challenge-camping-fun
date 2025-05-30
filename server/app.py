#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)
api=Api(app)


@app.route('/')
def home():
    return ''

class Campers(Resource):
    def get(self):
        campers= [camper.to_dict() for camper in Camper.query.all()]
        response= make_response(jsonify(campers),200)
        return response
    
    def post(self):
        data=request.get_json()
        errors =[]

        try:
            new_camper= Camper(
                name=data.get('name'),
                age= data.get('age')
            )
            db.session.add(new_camper)
            db.session.commit()
        except ValueError as e:
            errors.append(str(e))
            return make_response(jsonify({'errors':errors}),400)
        return make_response(jsonify(new_camper.to_dict()),201)
    
api.add_resource(Campers,'/campers')

class CamperById(Resource):
    def get(self,id):
        camper= Camper.query.filter_by(id=id).first()
        if not camper:
            return make_response(jsonify({'error':'Camper not found'}),404)
        response_data={
            'age':camper.age,
            'id':camper.id,
            'name':camper.name,
            'signups':[
                {
                    'activity_id':signup.activity_id,
                    'camper_id':signup.camper_id,
                    'id':signup.id,
                    'time':signup.time,
                    'activity':{
                        'difficulty':signup.activity.difficulty,
                        'id':signup.activity.id,
                        'name':signup.activity.name
                    }
                }for signup in camper.signups
            ]
        }
        return make_response(jsonify(response_data),200)
    
    def patch(self, id):
        camper = Camper.query.filter(Camper.id == id).first()
        if not camper:
            return make_response(jsonify({'error': 'Camper not found.'}), 404)

        data = request.get_json()

        try:
            if 'name' in data:
                if not data['name'].strip():
                    return make_response(jsonify({'errors': ['validation errors']}), 400)
                camper.name = data['name']
            if 'age' in data:
                if not isinstance(data['age'], int) or data['age'] < 8 or data['age'] > 18:
                    return make_response(jsonify({'errors': ['validation errors']}), 400)
                camper.age = data['age']
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'errors': ['validation errors']}), 400)

        response_data = {
            'id': camper.id,
            'name': camper.name,
            'age': camper.age
        }
        return make_response(jsonify(response_data), 202)
    
api.add_resource(CamperById,'/campers/<int:id>')

class Activities(Resource):
    def get(self):
        activities= [activity.to_dict() for activity in Activity.query.all()]
        return make_response(jsonify(activities),200)

api.add_resource(Activities,'/activities')

class ActivityById(Resource):
    def get(self,id):
        activity= Activity.query.get(id)
        if not activity:
            return make_response(jsonify({'error':'Activity not found'}),404)
        return make_response(jsonify(activity.to_dict()),200)
    
    def delete(self,id):
        activity= Activity.query.filter(Activity.id==id).first()
        if not activity:
            return make_response(jsonify({'error':'Activity not found'}),404)
        db.session.delete(activity)
        db.session.commit()
        return {},204

api.add_resource(ActivityById,'/activities/<int:id>')

class Signups(Resource):
    def post(self):
        data = request.get_json()
        errors = []

        camper_id = data.get('camper_id')
        activity_id = data.get('activity_id')
        time = data.get('time')

        # Basic validation
        if camper_id is None or activity_id is None or time is None:
            return make_response(jsonify({'errors': ['validation errors']}), 400)

        camper = Camper.query.get(camper_id)
        activity = Activity.query.get(activity_id)

        if not camper or not activity:
            if not camper:
                errors.append('camper not found')
            if not activity:
                errors.append('activity not found')
            return make_response(jsonify({'errors': errors}), 400)

        try:
            new_signup = Signup(
                camper_id=camper.id,
                activity_id=activity.id,
                time=time
            )
            db.session.add(new_signup)
            db.session.commit()

            response_data = {
                'id': new_signup.id,
                'camper_id': new_signup.camper_id,
                'activity_id': new_signup.activity_id,
                'time': new_signup.time,
                'activity': {
                    'difficulty': activity.difficulty,
                    'id': activity.id,
                    'name': activity.name
                },
                'camper': {
                    'age': camper.age,
                    'id': camper.id,
                    'name': camper.name
                }
            }
            return make_response(jsonify(response_data), 201)

        except Exception:
            db.session.rollback()
            return make_response(jsonify({'errors': ['validation errors']}), 400)

api.add_resource(Signups, '/signups')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
