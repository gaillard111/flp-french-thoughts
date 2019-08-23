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
     * Set javascript
     */
    public function configure()
    {
        $this->setTemplate('edit', 'ThoughtBundle:CRUD:edit_javascript.html.twig');
    }

    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('category', 'text')
            ->add('content')
            ->add('thoughtInfo')
            ->add('author', 'text')
            ->add('tags', 'text', array(
                'attr' => array(
                    'data-role' => 'tagsinput',
                ),
            ))
            ->add('published', null, array(
                'required' => false,
            ))
        ;
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
        foreach ($this->getFilterFields() as $filterField) {
            $datagridMapper->add($filterField);
        }
    }

    /**
     * @return array
     */
    public function getFilterFields()
    {
        return array(
            'category',
            'author',
            'tags',
        );
    }

    /**
     * @param RouteCollection $collection
     */
    protected function configureRoutes(RouteCollection $collection)
    {
        $collection
            ->add('publish', $this->getRouterIdParameter() . '/publish')
        ;
    }

    /**
     * {@inheritdoc}
     */
    public function getExportFormats()
    {
        return array(
            'txt',
            //'csv',
        );
    }

    /**
     * @return array
     */
    public function getExportFields()
    {
        return array(
            'id',
            'content',
            'tags',
            'author',
            'thoughtInfo',
            'category',
        );
    }
}
