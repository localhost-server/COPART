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
