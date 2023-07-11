(ns eliashaukssoncom.server
  (:require [ring.adapter.jetty :refer [run-jetty]]
            [eliashaukssoncom.handler :refer [app]]))

(defonce server (atom nil))

(defn start-server []
  (when (nil? @server)
    (reset! server (run-jetty #'app {:port 8080 :join? false}))))

(defn stop-server []
  (when (not (nil? @server))
    (.stop @server)
    (reset! server nil)))

(defn restart-server []
  (stop-server)
  (start-server))
