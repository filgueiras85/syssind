const db = require('../models/DBConnection');

module.exports = {
    async index () {
        const connection = await db.connect();
        
        const  [rows, fields] = await connection.execute('SELECT * FROM `listar_filiados`');

        return rows;
    },

    async show (id) {
        const connection = await db.connect();
        
        const  [rows, fields] = await connection.execute('SELECT * FROM `listar_filiados` WHERE `id_filiados` = ? ', [id]);

        return rows;
    }
}