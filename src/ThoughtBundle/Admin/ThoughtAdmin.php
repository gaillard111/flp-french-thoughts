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
class ThoughtAdmin extends Admin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('category')
            ->add('content')
            ->add('thoughtInfo')
            ->add('author')
            ->add('tags')
            ->add('published', null, array(
                'required' => false,
            ));
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('id')
            ->add('content')
            ->add('category')
            ->add('author')
            ->add('_action', 'action', array(
                'actions' => array(
                    'publish' => array(
                        'template' => 'ThoughtBundle:CRUD:list__publish_publish.html.twig',
                    ),
                ),
                'label'    => 'Published',
            ))
        ;
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        $datagridMapper
            ->add('category')
            ->add('author')
            ->add('tags')
        ;
    }

    /**
     * @param RouteCollection $collection
     */
    protected function configureRoutes(RouteCollection $collection)
    {
        $collection->add('publish', $this->getRouterIdParameter().'/publish');
    }
}
