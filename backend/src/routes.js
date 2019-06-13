const express = require('express');
const servidorController = require('./controllers/ServidorController')

const routes = new express.Router();

routes.get('/', async (req, res) => {
    let servidores = await servidorController.index();

    return res.send(servidores);
});

routes.get('/:id', async (req, res) => {
    let servidor = await servidorController.show(req.params.id);

    return res.send(servidor);
});

module.exports = routes;