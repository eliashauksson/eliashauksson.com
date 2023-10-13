(ns eliashaukssoncom.views.blog
  (:require [clojure.java.io :as io]
            [clojure.string :as string]
            [markdown-to-hiccup.core :refer [file->hiccup]]
            [cheshire.core :as json]
            [eliashaukssoncom.views.base :refer [base]]))

(defn blog-card [post]
  [:a.blog-post-card-link {:href (str "/blog/"
                                      (string/replace (last (string/split (:location post) #"/")) #".md" ""))}
   [:div.blog-post-card {:class (str "card-align-" (if (even? (Integer. (:id post)))
                                                     "left" "right"))}
    [:img.blog-post-card-image {:src (:image post)}]
    [:div.blog-post-card-content
     [:h1.blog-post-card-title (:title post)]
     [:p.blog-post-card-description (:description post)]
     [:div.blog-post-card-detail
      [:span.blog-post-card-detail-date
       [:i.fa.fa-calendar]
       [:p.blog-post-card-detail-date-text (:date post)]]
      [:span.blog-post-card-detail-author
       [:i.fa.fa-user]
       [:p.blog-post-card-detail-author-text (:author post)]]]]]])

(defn blog-content []
  [:div.blog-content
   [:div.blog-post-cards-list
    (let [json-str (slurp "resources/public/markdown/posts/all-posts.json")
          posts (json/parse-string json-str true)]
      (map blog-card (reverse posts)))]])

(defn render-post [name]
  [:div.blog-content
   (try [:div.blog-post
         [:a.blog-post-back-button {:href "/blog"} "Go back"]
         [:div.blog-post-content
          (file->hiccup (str "resources/public/markdown/posts/" name ".md"))]]
         (catch Exception e
           [:div.blog-post-not-found
            [:h2.blog-post-not-found-text "Error: The requested article could not be found."]]))])

(defn blog-page []
  (base (blog-content)))

(defn blog-post [name]
  (base (render-post name)))
