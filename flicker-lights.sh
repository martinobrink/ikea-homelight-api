#!/bin/sh

while [ True ]
do
  curl http://localhost:5000/turnon
  sleep 0.5
  curl http://localhost:5000/turnoff
  sleep 0.5
done