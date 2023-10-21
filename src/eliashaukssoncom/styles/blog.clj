(ns eliashaukssoncom.styles.blog
  (:require [garden.core :refer [css]]
            [garden.units :refer [px vh vw percent]]
            [garden.color :refer [rgb->hex]]
            [garden.stylesheet :refer [at-media]]
            [eliashaukssoncom.styles.colors :refer :all]))

(def blog-style
  (css
   [:.blog-content {:display "flex"
                    :flex-direction "column"
                    :justify-content "flex-start"
                    :align-items "center"
                    :background-color bg-color
                    :color fg-color
                    :min-height (vh 92)}]
   [:.blog-post {:max-width (px 1000)
                 :padding (px 30)
                 :margin-top (px 30)}]
   [:.blog-post-content
    [:h1 {:font-size (px 45)
          :margin-bottom (px 30)
          :margin-top (px 10)}]
    [:h2 {:font-size (px 30)
          :margin-bottom (px 20)
          :margin-top (px 20)}]
    [:p {:font-size (px 20)}]]
   [:.blog-post-back-button {:text-decoration "none"
                             :color bg-color
                             :background-color blue-color
                             :padding (px 12)
                             :font-weight "bold"
                             :font-size (px 20)
                             :border-color blue-color
                             :border-radius (px 8)}]
   [:.blog-post-details {:width (percent 100)
                         :margin-top (px 50)}]
   [:.blog-post-details-text {:font-size (px 20)
                              :color blue-color}]
   [:.blog-post-not-found {:display "flex"
                           :align-items "center"
                           :justify-content "center"
                           :height (vh 80)
                           :padding (px 80)}]
   [:.blog-post-not-found-text {:font-size (px 40)}]
   [:.blog-post-no-posts {:display "flex"
                          :align-items "center"
                          :justify-content "center"
                          :height (vh 80)
                          :padding (px 80)}]
   [:.blog-posts-no-posts-text {:font-size (px 40)}]
   [:.blog-post-cards-list {:max-width (px 1000)
                            :width (vw 80)
                            :margin "0 50px"
                            :margin-top (px 50)}]
   [:.blog-post-card-link {:text-decoration "none"
                           :color "inherit"
                           :cursor "pointer"}]
   [:.blog-post-card {:display "flex"
                      :width (percent 100)
                      :height (px 300)
                      :margin-bottom (px 50)
                      :box-shadow "rgba(50, 50, 93, 0.25) 0px 13px 27px -5px, rgba(0, 0, 0, 0.3) 0px 8px 16px -8px"}]
   [:.blog-post-card:hover {:transform "scale(1.01)"
                            :box-shadow "rgba(50, 50, 93, 0.25) 0px 15px 30px -5px, rgba(0, 0, 0, 0.3) 0px 10px 20px -8px"}]
   [:.card-align-left {:flex-direction "row"}]
   [:.card-align-right {:flex-direction "row-reverse"}]
   [:.blog-post-card-image {:width (percent 40)
                            :height (percent 100)
                            :object-fit "cover"}]
   [:.blog-post-card-content {:flex "0 0 60%"
                              :display "flex"
                              :flex-direction "column"
                              :padding (px 20)
                              :text-align "left"}]
   [:.blog-post-card-description {:flex-grow 1
                                  :margin-top (px 20)}]
   [:.blog-post-card-detail {:display "flex"
                             :justify-content "space-between"}
    [:span {:display "flex"
            :align-items "center"}
     [:i.fa {:color fg-color
             :margin-right (px 8)}]]]
   (at-media {:screen true
              :max-width (px 800)}
             [:.blog-post-card {:flex-direction "column"
                                :height (px 500)}]
             [:.blog-post-card-image {:width (percent 100)
                                      :height (percent 100)}])))
