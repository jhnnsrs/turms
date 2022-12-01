import useBaseUrl from "@docusaurus/useBaseUrl";
import React from "react";
import clsx from "clsx";
import styles from "./HomepageFeatures.module.css";

type FeatureItem = {
  title: string;
  image: string;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: "Pydantic",
    image: "/img/undraw_docusaurus_mountain.svg",
    description: (
      <>
        Turms makes it easy to build GraphQL API with Pydantic. It supports
        automatic validation, automatic documentation, and more.
      </>
    ),
  },
  {
    title: "Traitful",
    image: "/img/undraw_docusaurus_tree.svg",
    description: (
      <>
        Turms allows easy extensions of your GraphQL schema on the client side
        via additional bases (traits) based on the graphql type
      </>
    ),
  },
  {
    title: "Powered by Pure Python",
    image: "/img/undraw_docusaurus_react.svg",
    description: (
      <>
        Turms has minimal dependencies (only graphql-core for the 3.9 version),
        and is extensible via plugins.
      </>
    ),
  },
];

function Feature({ title, image, description }: FeatureItem) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center padding-horiz--md padding-top--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
