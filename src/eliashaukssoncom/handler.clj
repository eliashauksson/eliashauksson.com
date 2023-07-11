(ns eliashaukssoncom.handler
  (:require [ring.util.response :refer [redirect]]
            [ring.middleware.resource :refer [wrap-resource]]
            [compojure.core :refer [defroutes GET]]
            [compojure.route :refer [not-found]]
            [eliashaukssoncom.views.about :refer [about-page]]
            [eliashaukssoncom.views.nopage :refer [nopage-page]]))

(defroutes routes
  (GET "/" [] (redirect "/about"))
  (GET "/about" [] (about-page))
  (not-found (nopage-page)))

(def app
  (-> routes
      (wrap-resource "public")))
