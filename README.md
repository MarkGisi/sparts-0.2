## Utilizing the Blockchain to Establish Greater Trust in Open Source Software across the SupplyChain

### Introduction

The lion share of today’s software solutions are constructed from open source software.  In the data center it is typical for more than 80% of the software to be open source due to wide adoption of solutions such as Linux, various Apache offerings, MySQL, and Node.js, to name a few. Similarly, Embedded Software, which serves as the nervous system for many commercial products, is predominately comprised of Open Source (e.g., phones, watches, cameras, drones, self-driving automobiles …). 

Modern software solutions can be viewed as being comprised of many smaller reusable software sub-components, which intrinsically represents a new kind of intellectual “part”. A software part could simply consist of a few source files that compile to create a single program or library (atomic parts) or hundreds, if not thousands, of open source sub-parts that are combined to create much larger complex parts, such as a Linux runtime or an automobile braking sub-system (composite parts). Regardless of whether a software solution is simple or complex, it is important that we conceptualize each deliverable as a discrete unit or part. 

It is now more important than ever for software suppliers to maintain an accurate and complete list of the open source parts in their products in order to: 1) identify, review and secure the distribution rights (licenses) for each part; 2) understand the impact of an open source security vulnerability on a product (e.g., heartbleed bug); 3) enable identification of cryptography technologies (e.g., export licensing); and 4) enable accurate reporting on all open source parts as a requirement to obtain functional safety certification for safety critical product (e.g, automobiles, aircraft, elevators and medical devices).

Establishing trust on who did what, when and how within the supply chain with respect to open source is critical. That is, which suppliers created which parts and included which open source compliance artifacts for a given product. This is particularly challenging because we need to maintain global supply chain state information. We solved this problem by using Linux Foundation’s Hyperledger platform in order to create a Blockchain ledger that tracks which suppliers delivered which parts that used which open source for which products and who delivered (or did not deliver) which compliance artifacts. The main focus of this project is to deliver a Blockchain ledger to ensure a certain level of integrity is maintained with respect to using open source software across the supply chain. 

### Organization

1. **Sparts Software Parts Catalog** - A website application that plugs into the supply chain network that provides a catalog of the software parts. 
2. **Blockchain** **Ledger** - tracks all the open source parts and the meta data about the compliance artifacts of the open source parts. The Ledge r preserves the integrity and coordinates the of the compliance artifacts incluThe Ledger was built using the Hyperledger Sawtooth Process.
3. **Ledger Dashboard** - an application that enables one to monitor and administer the Ledger. 
4. **Conductor** - system service responsible for the managing the various components. 

In addition to the above four core services two addition important data structures were needed.

- Compliance Envelop - This is an archive of a collection of artifacts prepared to comply with or provide important information about the use of open source in a given software solution. 
- Open Source Software Bill of Materials (OSS BOM).  

