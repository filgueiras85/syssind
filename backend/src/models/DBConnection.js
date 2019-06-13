// get the client
const mysql = require('mysql2/promise');
 
module.exports = {
    // create the connection to database
    async connect() {
        return await mysql.createConnection({
            host: 'localhost',
            user: 'root',
            password: '',
            database: 'u680657591_sys'
        });
    }
}