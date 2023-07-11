(ns eliashaukssoncom.core
  (:require [eliashaukssoncom.server :refer [start-server]]))

(defn -main [& args]
  (start-server))
