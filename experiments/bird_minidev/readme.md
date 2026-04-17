# How to add a new BIRD database with QLever and GRASP
Set GRASP_INDEX_DIR to $PWD/grasp-indices
1. Add ntriples file to db/db_kg.nt - DONE
2. Copy Qleverfile from movie/Qleverfile to db/Qleverfile - DONE
3. Set name to db and port to some free port in the Qleverfile
4. Run qlever index and qlever start
5. Run grasp data db --endpoint http://localhost:port
6. Run grasp index db
7. (Optional) Add prefixes.json to $GRASP_INDEX_DIR/db/prefixes.json to tell GRASP
the prefixes used in the knowledge graph.
See [$GRASP_INDEX_DIR/movie/prefixes.json](grasp-indices/movie/prefixes.json)
for an example.
8. Add knowledge graph to serve.yaml with kg: db and endpoint: http://localhost:port
9. Restart GRASP server with grasp --log-level DEBUG serve serve.yaml --port 10001