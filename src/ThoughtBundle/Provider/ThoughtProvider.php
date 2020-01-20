<?php

namespace ThoughtBundle\Provider;

use Elastica\Document;
use Elastica\Type;
use FOS\ElasticaBundle\Provider\ProviderInterface;

/**
 * Class ThoughtProvider
 *
 * @package ThoughtBundle\Provider
 */
class ThoughtProvider // implements ProviderInterface
{
    //protected $thoughtType;

    /**
     * ThoughtProvider constructor.
     *
     * @param Type $thoughtType
     */
    /*public function __construct(Type $thoughtType)
    {
        $this->thoughtType = $thoughtType;
    }*/

    /**
     * Insert the repository objects in the type index
     *
     * @param \Closure $loggerClosure
     * @param array    $options
     */
    /*public function populate(\Closure $loggerClosure = null, array $options = array())
    {
        if ($loggerClosure) {
            $loggerClosure('Indexing thoughts');
        }

        $document = new Document();
        $document->setData(array('username' => 'Bob'));
        $this->thoughtType->addDocuments(array($document));
    }*/
}