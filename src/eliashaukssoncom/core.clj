(ns eliashaukssoncom.core
  (:gen-class)
  (:require [eliashaukssoncom.server :refer [start-server]]))

(defn -main [& args]
  (start-server))
