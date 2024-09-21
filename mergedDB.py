from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

client = MongoClient('mongodb://adminUser:securePassword@45.56.127.88/?authSource=admin&tls=false')
result = client['Copart']['IntegratedData'].aggregate([
    {
        '$project': {
            'SoldOn': 'Copart', 
            'prices': 1, 
            'Name': '$Info.Name', 
            'Year': {
                '$arrayElemAt': [
                    {
                        '$split': [
                            '$Info.Name', ' '
                        ]
                    }, 0
                ]
            }, 
            'Make': {
                '$let': {
                    'vars': {
                        'secondWord': {
                            '$arrayElemAt': [
                                {
                                    '$split': [
                                        '$Info.Name', ' '
                                    ]
                                }, 1
                            ]
                        }
                    }, 
                    'in': {
                        '$switch': {
                            'branches': [
                                {
                                    'case': {
                                        '$eq': [
                                            '$$secondWord', 'ALFA'
                                        ]
                                    }, 
                                    'then': 'ALFA ROMEO'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$$secondWord', 'ASTON'
                                        ]
                                    }, 
                                    'then': 'ASTON MARTIN'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$$secondWord', 'LAND'
                                        ]
                                    }, 
                                    'then': 'LAND ROVER'
                                }, {
                                    'case': {
                                        '$eq': [
                                            '$$secondWord', 'AMERICAN'
                                        ]
                                    }, 
                                    'then': 'AMERICAN MOTORS'
                                }
                            ], 
                            'default': '$$secondWord'
                        }
                    }
                }
            }, 
            'Images': '$Info.Images', 
            'Lot Number': '$Info.Vehicle Info.Lot Number', 
            'VIN': '$Info.Vehicle Info.VIN', 
            'Title Code': '$Info.Vehicle Info.Title Code', 
            'Odometer': {
                '$arrayElemAt': [
                    {
                        '$split': [
                            '$Info.Vehicle Info.Odometer', ' '
                        ]
                    }, 0
                ]
            }, 
            'Primary Damage': '$Info.Vehicle Info.Primary Damage', 
            'Secondary Damage': '$Info.Vehicle Info.Secondary Damage', 
            'Cylinders': '$Info.Vehicle Info.Cylinders', 
            'Color': '$Info.Vehicle Info.Color', 
            'Engine Type': {
                '$arrayElemAt': [
                    {
                        '$split': [
                            '$Info.Vehicle Info.Engine Type', ' '
                        ]
                    }, 0
                ]
            }, 
            'Drive': '$Info.Vehicle Info.Drive', 
            'Vehicle Type': '$Info.Vehicle Info.Vehicle Type', 
            'Sale Name': '$Info.Sale Info.Sale Name', 
            'Highlights': '$Info.Vehicle Info.Highlights'
        }
    }, {
        '$project': {
            'SoldOn': 1, 
            'prices': 1, 
            'Name': 1, 
            'Year': 1, 
            'Make': 1, 
            'remaining_string': {
                '$trim': {
                    'input': {
                        '$replaceOne': {
                            'input': '$Name', 
                            'find': {
                                '$concat': [
                                    '$Year', ' ', '$Make'
                                ]
                            }, 
                            'replacement': ''
                        }
                    }
                }
            }, 
            'Images': 1, 
            'Lot Number': 1, 
            'VIN': 1, 
            'Title Code': 1, 
            'Odometer': 1, 
            'Primary Damage': 1, 
            'Secondary Damage': 1, 
            'Cylinders': 1, 
            'Color': 1, 
            'Engine Type': 1, 
            'Drive': 1, 
            'Vehicle Type': 1, 
            'Sale Name': 1, 
            'Highlights': 1
        }
    }, {
        '$project': {
            'SoldOn': 1, 
            'prices': 1, 
            'Name': 1, 
            'Year': 1, 
            'Make': 1, 
            'Model': {
                '$let': {
                    'vars': {
                        'matchedModel': {
                            '$filter': {
                                'input': [
                                    '718 BOXSTER', 'NEW BEETLE', 'LAND CRUISER', 'MODEL S', 'MODEL X', 'MODEL Y', 'MODEL 3', 'GRAND VITARA', '718 CAYMAN', '3000 GT', 'AMG GT', 'TOWN CAR', 'GRAND WAGONEER', 'SANTA FE', 'SANTA CRUZ', 'CROWN VICTORIA', '458 ITALIA', 'RAM 3500', 'RAM 2500', 'RAM 1500', 'GRAND CARAVAN', 'MONTE CARLO', 'EL CAMINO', 'PARK AVENUE', 'GRAND CHEROKEE', 'RANGE ROVER'
                                ], 
                                'as': 'model', 
                                'cond': {
                                    '$regexMatch': {
                                        'input': '$remaining_string', 
                                        'regex': {
                                            '$concat': [
                                                '\\b', '$$model', '\\b'
                                            ]
                                        }, 
                                        'options': 'i'
                                    }
                                }
                            }
                        }
                    }, 
                    'in': {
                        '$cond': {
                            'if': {
                                '$gt': [
                                    {
                                        '$size': '$$matchedModel'
                                    }, 0
                                ]
                            }, 
                            'then': {
                                '$arrayElemAt': [
                                    '$$matchedModel', 0
                                ]
                            }, 
                            'else': {
                                '$arrayElemAt': [
                                    {
                                        '$split': [
                                            '$remaining_string', ' '
                                        ]
                                    }, 0
                                ]
                            }
                        }
                    }
                }
            }, 
            'Images': 1, 
            'Lot Number': 1, 
            'VIN': 1, 
            'Title Code': 1, 
            'Odometer': 1, 
            'Primary Damage': 1, 
            'Secondary Damage': 1, 
            'Cylinders': 1, 
            'Color': 1, 
            'Engine Type': 1, 
            'Drive': 1, 
            'Vehicle Type': 1, 
            'Sale Name': 1, 
            'Highlights': 1
        }
    }, {
        '$project': {
            'SoldOn': 1, 
            'prices': 1, 
            'Name': 1, 
            'Year': {
                '$convert': {
                    'input': '$Year', 
                    'to': 'int', 
                    'onError': None, 
                    'onNull': None
                }
            }, 
            'Make': 1, 
            'Model': 1, 
            'Model2': {
                '$trim': {
                    'input': {
                        '$replaceOne': {
                            'input': '$Name', 
                            'find': {
                                '$concat': [
                                    {
                                        '$toString': {
                                            '$convert': {
                                                'input': '$Year', 
                                                'to': 'string', 
                                                'onError': '', 
                                                'onNull': ''
                                            }
                                        }
                                    }, ' ', '$Make', ' ', '$Model'
                                ]
                            }, 
                            'replacement': ''
                        }
                    }
                }
            }, 
            'Images': 1, 
            'Lot Number': 1, 
            'VIN': 1, 
            'Title Code': 1, 
            'Odometer': 1, 
            'Primary Damage': 1, 
            'Secondary Damage': 1, 
            'Cylinders': 1, 
            'Color': 1, 
            'Engine Type': 1, 
            'Drive': 1, 
            'Vehicle Type': 1, 
            'Sale Name': 1, 
            'Highlights': 1
        }
    }, {
        '$project': {
            'SoldOn': 1, 
            'prices': 1, 
            'Name': 1, 
            'Year': {
                '$convert': {
                    'input': '$Year', 
                    'to': 'int', 
                    'onError': None, 
                    'onNull': None
                }
            }, 
            'Make': 1, 
            'Model': 1, 
            'Model2': 1, 
            'Images': 1, 
            'Lot Number': 1, 
            'VIN': 1, 
            'Title Code': 1, 
            'Odometer': 1, 
            'Primary Damage': 1, 
            'Secondary Damage': 1, 
            'Cylinders': 1, 
            'Color': 1, 
            'Engine Type': 1, 
            'Drive': 1, 
            'Vehicle Type': 1, 
            'Sale Name': 1, 
            'Highlights': 1
        }
    }, {
        '$merge': {
            'into': {
                'db': 'MergedDB', 
                'coll': 'IaaiCopart'
            }, 
            'whenMatched': 'replace', 
            'whenNotMatched': 'insert'
        }
    }
])
