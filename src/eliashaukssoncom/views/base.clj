(ns eliashaukssoncom.views.base
  (:require [clojure.string :refer [join]]
            [hiccup.page :refer [html5]]
            [eliashaukssoncom.styles.base :refer [base-style]]
            [eliashaukssoncom.styles.about :refer [about-style]]))

(def toggle-script
  (join "\n"
        ["const navSlide = () => {"
         "    const burger = document.querySelector('.burger');"
         "    const nav = document.querySelector('.nav-links');"
         "    const navLinks = document.querySelectorAll('.nav-links li');"
         "    burger.addEventListener('click',()=>{"
         "        nav.classList.toggle('nav-active');"
         "        navLinks.forEach((link,index)=>{"
         "            link.style.animation = `navLinkFade 0.5s ease forwards 0`"
         "        });"
         "        burger.classList.toggle('toggle');"
         "    });"
         "}"
         "navSlide();"]))
  

(defn base [content]
  (html5
   [:head
    [:title "Elías Hauksson"]
    [:meta {:name "description"
            :content "Personal Website of Elías Hauksson."}]
    [:meta {:name "author"
            :content "Elías Hauksson"}]
    [:meta {:charset "utf-8"}]
    [:meta {:name "viewport"
            :content "width=device-width, initial-scale=1"}]
    [:meta {:property "og:title"
            :content "Elías Hauksson"}]
    [:meta {:property "og:type"
            :content "website"}]
    [:meta {:property "og:url"
            :content "https://eliashauksson.com"}]
    [:meta {:property "og:description"
            :content "Personal Website of Elías Hauksson."}]
    [:link {:rel "preconnect"
            :href "https://fonts.googleapis.com"}]
    [:link {:rel "preconnect"
            :href "https://fonts.gstatic.com"}]
    [:link {:rel "stylesheet"
            :href "https://fontsgoogleapis.com/css2?family=Montserrat&display=swap"}]
    [:link {:rel "icon"
            :type "image/png"
            :href "images/favicon.png"}]
    [:style base-style]
    [:style about-style]
    [:script {:crossorigin "anonymous"
              :src "https://kit.fontawesome.com/2c8cb2c49d.js"}]]
   [:body
    [:nav
     [:div.logo
      [:h4 [:a {:href "/"} "Elías Hauksson"]]]
     [:ul.nav-links
      [:li [:a {:href "/about"} "About"]]]
     [:div.burger
      [:div.line1]
      [:div.line2]
      [:div.line3]]]
    (content)
    [:script toggle-script]]))
