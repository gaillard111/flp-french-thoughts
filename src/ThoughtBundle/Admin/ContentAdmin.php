<?php

namespace ThoughtBundle\Admin;

use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Show\ShowMapper;
use Sonata\AdminBundle\Route\RouteCollection;

/**
 * Class ThoughtAdmin
 * @package ThoughtBundle\Admin
 */
class ContentAdmin extends Admin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title', 'text')
            ->add('content', 'sonata_formatter_type', array(
                'event_dispatcher' => $formMapper->getFormBuilder()->getEventDispatcher(),
                'format_field'     => 'formatType',
                'source_field'     => 'content',
                'source_field_options'      => array(
                    'attr' => array('class' => 'span10', 'rows' => 20),
                ),
                'format_field_options' => array(
                    'choices' => array(
                        'richhtml' => 'richhtml',
                    ),
                ),
                'listener'       => true,
                'target_field'   => 'content',
            ));
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('title')
            ->add('content')
        ;
    }

    protected function configureRoutes(RouteCollection $collection)
    {
        // All routes are removed
        $collection->clearExcept(array('edit', 'list'));
    }
}
