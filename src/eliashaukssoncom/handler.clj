(ns eliashaukssoncom.handler
  (:require [ring.util.response :refer [redirect]]
            [ring.middleware.resource :refer [wrap-resource]]
            [ring.middleware.content-type :refer [wrap-content-type]]
            [clojure.java.io :as io]
            [compojure.core :refer [defroutes GET]]
            [compojure.route :refer [not-found]]
            [eliashaukssoncom.views.about :refer [about-page]]
            [eliashaukssoncom.views.blog :refer [blog-page blog-post]]
            [eliashaukssoncom.views.nopage :refer [nopage-page]]))

(defroutes routes
  (GET "/" [] (redirect "/about"))
  (GET "/about" [] (about-page))
  (GET "/blog" [] (blog-page))
  (GET "/blog/:post-name" [post-name] (blog-post post-name))
  (not-found (nopage-page)))

(def app
  (-> routes
      (wrap-content-type)
      (wrap-resource "public")))
